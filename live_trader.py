"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

#!/usr/bin/env python3
"""
Live Trading System - Main Orchestrator
Connects all components and runs the event-driven trading loop.
"""

import sys
import signal
import time
import logging
from datetime import datetime

from utils import setup_logging, get_ny_time, is_market_open
from candle_buffer import CandleBuffer
from session_state import SessionStateMachine
from entry_detector import EntryDetector
from oanda_executor import OandaExecutor
from streaming_client import StreamingClient
from config import INSTRUMENT

logger = None


class LiveTrader:
    """
    Main live trading orchestrator.
    Coordinates all components and runs the event loop.
    """
    
    def __init__(self, dry_run=False):
        """
        Initialize live trader.
        
        Args:
            dry_run (bool): If True, log signals but don't execute orders
        """
        self.dry_run = dry_run
        
        # Initialize components
        self.candle_buffer = CandleBuffer()
        self.session_state = SessionStateMachine()
        self.entry_detector = EntryDetector()
        self.executor = OandaExecutor(dry_run=dry_run)
        self.streaming_client = None
        
        # Track last processed candle
        self.last_candle_time = None
        
        # Shutdown flag
        self.running = False
        
        logger.info(f"LiveTrader initialized (dry_run={dry_run})")
    
    def start(self):
        """Start the live trading system."""
        logger.info("=" * 60)
        logger.info("🚀 Starting Live Trading System")
        logger.info(f"   Instrument: {INSTRUMENT}")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        logger.info("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start streaming client
        self.streaming_client = StreamingClient(on_tick_callback=self._on_tick)
        self.streaming_client.start()
        
        self.running = True
        
        # Main event loop
        self._event_loop()
    
    def _on_tick(self, timestamp, bid, ask):
        """
        Callback for each tick from streaming client.
        
        Args:
            timestamp (datetime): Tick timestamp
            bid (float): Bid price
            ask (float): Ask price
        """
        # Add tick to candle buffer
        self.candle_buffer.add_tick(timestamp, bid, ask)
    
    def _event_loop(self):
        """Main event loop - runs continuously."""
        logger.info("Event loop started")
        
        while self.running:
            try:
                # Check if market is open
                if not is_market_open():
                    time.sleep(60)  # Check every minute
                    continue
                
                # Store previous state to detect resets
                prev_date = self.session_state.current_date
                
                # Update session state
                self.session_state.update(self.candle_buffer)
                
                # Reset entry detector if new day started
                if self.session_state.current_date != prev_date and prev_date is not None:
                    logger.info("New trading day detected - resetting entry detector")
                    self.entry_detector.reset()
                
                # Check for new 1m candle
                latest_candles = self.candle_buffer.get_latest_1m(1)
                if len(latest_candles) > 0:
                    latest_candle = latest_candles[0]
                    
                    # Process new candle if we haven't seen it yet
                    if self.last_candle_time is None or latest_candle.timestamp > self.last_candle_time:
                        self._process_new_candle(latest_candle)
                        self.last_candle_time = latest_candle.timestamp
                
                # Monitor open position
                if self.executor.has_position():
                    self._monitor_position()
                
                # Sleep briefly to avoid busy loop
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in event loop: {e}", exc_info=True)
                time.sleep(5)
        
        logger.info("Event loop stopped")
    
    def _process_new_candle(self, candle):
        """
        Process a new 1-minute candle.
        
        Args:
            candle (Candle): New candle
        """
        logger.debug(f"New candle: {candle}")
        
        # Check if we can trade
        if not self.session_state.can_trade():
            return
        
        # Get OR range
        or_high, or_low = self.session_state.get_or_range()
        
        if or_high is None or or_low is None:
            return
        
        # Process candle through entry detector
        signal = self.entry_detector.process_candle(candle, or_high, or_low)
        
        # If we got an entry signal, execute trade
        if signal is not None:
            logger.info("=" * 60)
            logger.info("📊 ENTRY SIGNAL DETECTED!")
            logger.info(f"   Model: {signal['model']}")
            logger.info(f"   Direction: {signal['direction'].upper()}")
            logger.info(f"   Entry: {signal['entry_price']:.2f}")
            logger.info(f"   SL: {signal['sl']:.2f}")
            logger.info(f"   TP: {signal['tp']:.2f}")
            logger.info("=" * 60)
            
            # Place order
            success = self.executor.place_order(signal)
            
            if success:
                # Mark trade taken in session state
                self.session_state.mark_trade_taken()
                logger.info("✅ Trade executed - session closed")
            else:
                logger.error("❌ Trade execution failed")
    
    def _monitor_position(self):
        """Monitor open position for exit."""
        # Check if position was closed by OANDA
        if self.executor.check_if_closed():
            logger.info("Position closed - session ended")
            self.session_state.mark_trade_taken()
            return
        
        # Get current price from latest candle
        latest = self.candle_buffer.get_latest_1m(1)
        if len(latest) > 0:
            current_price = latest[0].close
            
            # Monitor for exit
            result = self.executor.monitor_position(current_price)
            
            if result is not None:
                logger.info(f"Position exited: {result}")
                self.session_state.mark_trade_taken()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\n⚠️  Received signal {signum} - shutting down gracefully...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the system."""
        logger.info("Shutting down...")
        
        self.running = False
        
        # Stop streaming
        if self.streaming_client:
            self.streaming_client.stop()
        
        # Close any open positions
        if self.executor.has_position():
            logger.warning("Closing open position before shutdown...")
            self.executor.force_close_position()
        
        # Print account summary
        summary = self.executor.get_account_summary()
        if summary:
            logger.info("=" * 60)
            logger.info("📊 Account Summary:")
            logger.info(f"   Balance: {summary.get('balance', 'N/A')}")
            logger.info(f"   P/L: {summary.get('pl', 'N/A')}")
            logger.info("=" * 60)
        
        logger.info("✅ Shutdown complete")
        sys.exit(0)


def main():
    """Main entry point."""
    global logger
    
    # Setup logging
    logger = setup_logging()
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        logger.info("⚠️  Running in DRY RUN mode - no real orders will be placed")
    
    # Create and start trader
    trader = LiveTrader(dry_run=dry_run)
    
    try:
        trader.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Keyboard interrupt received")
        trader.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        trader.shutdown()


if __name__ == "__main__":
    main()
