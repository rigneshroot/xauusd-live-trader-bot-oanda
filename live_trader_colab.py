"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

#!/usr/bin/env python3
"""
Live Trading System - Google Colab Compatible Version
Single-file implementation using polling instead of streaming.

USAGE IN COLAB:
1. Upload this file or paste into a cell
2. Run: !pip install oandapyV20 pandas pytz
3. Set dry_run=True for testing
4. Run the main() function

This will run until:
- A trade is taken
- Market closes (16:00 NY)
- You stop the cell
"""

import oandapyV20
from oandapyV20.endpoints import instruments, orders, positions
import pandas as pd
import datetime
import pytz
import time
import logging
from collections import deque
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

OANDA_ACCOUNT_ID = ''
OANDA_ACCESS_TOKEN = ''

INSTRUMENT = 'XAU_USD'
UNITS = 3
RISK_REWARD = 2

# Strategy Parameters
SKIP_FIRST_N = 5
FVG_LOOKBACK = 3
RETEST_PCT = 0.05

# Session Times (NY timezone)
SESSION_START = datetime.time(9, 30)
OR_LOCK_TIME = datetime.time(9, 35)
SESSION_END = datetime.time(16, 0)

# Polling interval (seconds)
POLL_INTERVAL = 60  # Fetch new candle every minute

# Optimization: Only fetch recent candles (not full history)
CANDLE_FETCH_COUNT = 20  # Reduced from 100 (80% bandwidth savings)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_ny_time():
    """Get current time in New York timezone."""
    ny_tz = pytz.timezone('America/New_York')
    return datetime.datetime.now(ny_tz)

def is_market_open():
    """Check if market is currently open."""
    ny_time = get_ny_time()
    if ny_time.weekday() >= 5:  # Weekend
        return False
    return SESSION_START <= ny_time.time() <= SESSION_END

# ============================================================================
# CANDLE CLASS
# ============================================================================

class Candle:
    """Represents a single OHLCV candle."""
    def __init__(self, timestamp, open_price, high, low, close, volume=0):
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
    
    def __repr__(self):
        return f"Candle({self.timestamp}, O:{self.open:.2f}, H:{self.high:.2f}, L:{self.low:.2f}, C:{self.close:.2f})"

# ============================================================================
# SESSION STATE MACHINE
# ============================================================================

class SessionState(Enum):
    PRE_OR = "PRE_OR"
    OR_BUILDING = "OR_BUILDING"
    OR_LOCKED = "OR_LOCKED"
    POST_OR_TRADING = "POST_OR_TRADING"
    SESSION_CLOSED = "SESSION_CLOSED"

class SessionStateMachine:
    """Manages trading session states."""
    def __init__(self):
        self.state = SessionState.PRE_OR
        self.or_high = None
        self.or_low = None
        self.trade_taken = False
        self.current_date = None
        logger.info("Session state: PRE_OR")
    
    def update(self, candles_5m):
        """Update state based on current time and candles."""
        ny_time = get_ny_time()
        current_time = ny_time.time()
        current_date = ny_time.date()
        
        # Reset for new day
        if self.current_date != current_date:
            self._reset_for_new_day(current_date)
        
        if self.state == SessionState.PRE_OR and current_time >= SESSION_START:
            self.state = SessionState.OR_BUILDING
            logger.info("State transition: PRE_OR -> OR_BUILDING")
        
        elif self.state == SessionState.OR_BUILDING and current_time >= OR_LOCK_TIME:
            # Calculate OR from 5m candles
            or_candles = [c for c in candles_5m if 
                         c.timestamp.date() == current_date and
                         datetime.time(9, 30) <= c.timestamp.time() <= datetime.time(9, 34)]
            
            if or_candles:
                self.or_high = max(c.high for c in or_candles)
                self.or_low = min(c.low for c in or_candles)
                logger.info(f"OR LOCKED | High: {self.or_high:.2f} | Low: {self.or_low:.2f}")
                self.state = SessionState.OR_LOCKED
        
        elif self.state == SessionState.OR_LOCKED:
            self.state = SessionState.POST_OR_TRADING
            logger.info("State transition: OR_LOCKED -> POST_OR_TRADING")
        
        elif self.state == SessionState.POST_OR_TRADING and current_time >= SESSION_END:
            self.state = SessionState.SESSION_CLOSED
            logger.info("State transition: POST_OR_TRADING -> SESSION_CLOSED")
    
    def _reset_for_new_day(self, new_date):
        logger.info(f"Resetting for new day: {new_date}")
        self.state = SessionState.PRE_OR
        self.or_high = None
        self.or_low = None
        self.trade_taken = False
        self.current_date = new_date
    
    def can_trade(self):
        return (self.state == SessionState.POST_OR_TRADING and 
                not self.trade_taken and 
                self.or_high is not None)
    
    def mark_trade_taken(self):
        self.trade_taken = True
        self.state = SessionState.SESSION_CLOSED
        logger.info("Trade taken - session closed")

# ============================================================================
# ENTRY DETECTOR
# ============================================================================

class EntryDetector:
    """Stateful entry detection."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.breakout_seen = False
        self.breakout_direction = None
        self.retest_active = False
        self.retest_candle = None
        self.confirmed = False
        self.invalidated = False
        self.entry_signal = None
        self.candle_history = []
        self.candles_since_or_lock = 0
        self.or_high = None
        self.or_low = None
        self.or_range = None
    
    def process_candle(self, candle, or_high, or_low):
        """Process single candle."""
        if self.or_high is None:
            self.or_high = or_high
            self.or_low = or_low
            self.or_range = or_high - or_low
        
        self.candle_history.append(candle)
        self.candles_since_or_lock += 1
        
        if self.candles_since_or_lock <= SKIP_FIRST_N:
            return None
        
        if self.confirmed or self.invalidated:
            return self.entry_signal
        
        if not self.breakout_seen:
            self._check_breakout(candle)
        elif self.breakout_seen and not self.retest_active:
            self._check_retest(candle)
        elif self.retest_active:
            self._check_confirmation(candle)
        
        # Try FVG if no retest
        if (self.breakout_seen and not self.retest_active and 
            len(self.candle_history) >= 15):
            self._check_fvg()
        
        return self.entry_signal
    
    def _check_breakout(self, candle):
        if candle.close > self.or_high:
            self.breakout_seen = True
            self.breakout_direction = 'long'
            logger.info(f"BREAKOUT LONG at {candle.timestamp}")
        elif candle.close < self.or_low:
            self.breakout_seen = True
            self.breakout_direction = 'short'
            logger.info(f"BREAKOUT SHORT at {candle.timestamp}")
    
    def _check_retest(self, candle):
        tol = self.or_range * RETEST_PCT
        anchor = self.or_high if self.breakout_direction == 'long' else self.or_low
        band_low = anchor - tol
        band_high = anchor + tol
        
        # Invalidation
        if self.breakout_direction == 'long' and candle.close < self.or_high:
            self.invalidated = True
            logger.info("INVALIDATED: Re-entered OR")
            return
        if self.breakout_direction == 'short' and candle.close > self.or_low:
            self.invalidated = True
            logger.info("INVALIDATED: Re-entered OR")
            return
        
        # Retest check
        entered = ((candle.low <= band_high and candle.high >= band_low) if self.breakout_direction == 'long'
                  else (candle.high >= band_low and candle.low <= band_high))
        
        if entered:
            self.retest_active = True
            self.retest_candle = candle
            logger.info(f"RETEST detected at {candle.timestamp}")
    
    def _check_confirmation(self, candle):
        if not self.retest_candle or len(self.candle_history) < 2:
            return
        
        tol = self.or_range * RETEST_PCT
        anchor = self.or_high if self.breakout_direction == 'long' else self.or_low
        band_low = anchor - tol
        band_high = anchor + tol
        
        # Invalidation
        if self.breakout_direction == 'long' and candle.low < band_low:
            self.invalidated = True
            return
        if self.breakout_direction == 'short' and candle.high > band_high:
            self.invalidated = True
            return
        
        prev = self.candle_history[-2]
        cons_low = self.retest_candle.low - tol
        cons_high = self.retest_candle.high + tol
        
        body_ratio = abs(candle.close - candle.open) / max(candle.high - candle.low, 0.0001)
        
        displacement = False
        if self.breakout_direction == 'long':
            displacement = (candle.close > cons_high and candle.close > prev.close and
                          candle.high > prev.high and body_ratio >= 0.30)
        else:
            displacement = (candle.close < cons_low and candle.close < prev.close and
                          candle.low < prev.low and body_ratio >= 0.30)
        
        if displacement:
            self.confirmed = True
            self._generate_signal(candle, model=1)
            logger.info(f"CONFIRMED Model 1 | Entry: {candle.close:.2f}")
    
    def _check_fvg(self):
        for i in range(len(self.candle_history) - FVG_LOOKBACK + 1):
            block = self.candle_history[i:i + FVG_LOOKBACK]
            if self.breakout_direction == 'long' and block[0].high < block[-1].low:
                self.confirmed = True
                self._generate_signal(block[-1], model=2)
                logger.info(f"CONFIRMED Model 2 (FVG)")
                return
            elif self.breakout_direction == 'short' and block[0].low > block[-1].high:
                self.confirmed = True
                self._generate_signal(block[-1], model=2)
                logger.info(f"CONFIRMED Model 2 (FVG)")
                return
    
    def _generate_signal(self, candle, model):
        entry = candle.close
        
        if model == 1 and self.retest_candle:
            if self.breakout_direction == 'long':
                sl = self.retest_candle.low
                if sl >= entry:
                    sl = entry - 0.50
                tp = entry + (2 * (entry - sl))
            else:
                sl = self.retest_candle.high
                if sl <= entry:
                    sl = entry + 0.50
                tp = entry - (2 * (sl - entry))
        else:
            recent = self.candle_history[-14:]
            atr = sum(c.high - c.low for c in recent) / len(recent)
            sl_dist = 0.8 * atr
            if self.breakout_direction == 'long':
                sl = entry - sl_dist
                tp = entry + (2 * sl_dist)
            else:
                sl = entry + sl_dist
                tp = entry - (2 * sl_dist)
        
        self.entry_signal = {
            'model': model,
            'direction': self.breakout_direction,
            'entry_price': entry,
            'sl': sl,
            'tp': tp
        }

# ============================================================================
# OANDA EXECUTOR
# ============================================================================

class OandaExecutor:
    """Execute trades via OANDA."""
    def __init__(self, dry_run=False):
        self.client = oandapyV20.API(access_token=OANDA_ACCESS_TOKEN)
        self.dry_run = dry_run
        self.current_position = None
        logger.info(f"Executor initialized (dry_run={dry_run})")
    
    def place_order(self, signal):
        """Place market order with SL/TP."""
        direction = signal['direction']
        entry = signal['entry_price']
        sl = signal['sl']
        tp = signal['tp']
        
        units = UNITS if direction == 'long' else -UNITS
        
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Placing {direction.upper()} order:")
        logger.info(f"  Entry: {entry:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
        
        if self.dry_run:
            self.current_position = signal
            return True
        
        try:
            order_data = {
                "order": {
                    "instrument": INSTRUMENT,
                    "units": str(units),
                    "type": "MARKET",
                    "stopLossOnFill": {"price": f"{sl:.2f}"},
                    "takeProfitOnFill": {"price": f"{tp:.2f}"}
                }
            }
            
            r = orders.OrderCreate(accountID=OANDA_ACCOUNT_ID, data=order_data)
            response = self.client.request(r)
            
            self.current_position = signal
            logger.info(f"✅ Order placed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return False
    
    def has_position(self):
        return self.current_position is not None

# ============================================================================
# DATA FETCHER
# ============================================================================

def fetch_recent_candles(instrument, granularity, count=100):
    """Fetch recent candles from OANDA."""
    client = oandapyV20.API(access_token=OANDA_ACCESS_TOKEN)
    
    params = {
        "granularity": granularity,
        "count": count,
        "price": "M"
    }
    
    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    client.request(r)
    
    candles = []
    for c in r.response.get("candles", []):
        ny_tz = pytz.timezone('America/New_York')
        timestamp = pd.to_datetime(c["time"]).tz_convert(ny_tz)
        
        candle = Candle(
            timestamp=timestamp,
            open_price=float(c["mid"]["o"]),
            high=float(c["mid"]["h"]),
            low=float(c["mid"]["l"]),
            close=float(c["mid"]["c"]),
            volume=int(c["volume"])
        )
        candles.append(candle)
    
    return candles

# ============================================================================
# MAIN LIVE TRADER
# ============================================================================

def main(dry_run=True):
    """
    Main live trading loop for Google Colab.
    
    Args:
        dry_run (bool): If True, log signals but don't execute orders
    """
    logger.info("=" * 60)
    logger.info("🚀 Live Trading System (Colab Version)")
    logger.info(f"   Mode: {'DRY RUN' if dry_run else 'LIVE TRADING'}")
    logger.info("=" * 60)
    
    # Initialize components
    session_state = SessionStateMachine()
    entry_detector = EntryDetector()
    executor = OandaExecutor(dry_run=dry_run)
    
    # Track processed candles
    processed_1m = set()
    
    try:
        while True:
            # Check market hours
            if not is_market_open():
                logger.info("Market closed - waiting...")
                time.sleep(300)  # Check every 5 minutes
                continue
            
            # Fetch recent candles (optimized: only fetch what we need)
            candles_1m = fetch_recent_candles(INSTRUMENT, "M1", count=CANDLE_FETCH_COUNT)
            candles_5m = fetch_recent_candles(INSTRUMENT, "M5", count=10)
            
            # Update session state
            session_state.update(candles_5m)
            
            # If session closed, stop
            if session_state.state == SessionState.SESSION_CLOSED:
                logger.info("Session closed - stopping")
                break
            
            # Process new 1m candles
            if session_state.can_trade():
                for candle in candles_1m:
                    candle_id = (candle.timestamp, candle.close)
                    
                    if candle_id not in processed_1m:
                        processed_1m.add(candle_id)
                        
                        signal = entry_detector.process_candle(
                            candle, 
                            session_state.or_high, 
                            session_state.or_low
                        )
                        
                        if signal:
                            logger.info("=" * 60)
                            logger.info("📊 ENTRY SIGNAL!")
                            logger.info(f"   Model: {signal['model']}")
                            logger.info(f"   Direction: {signal['direction'].upper()}")
                            logger.info(f"   Entry: {signal['entry_price']:.2f}")
                            logger.info("=" * 60)
                            
                            if executor.place_order(signal):
                                session_state.mark_trade_taken()
                                logger.info("✅ Trade executed - session ended")
                                return
            
            # Wait before next poll
            logger.info(f"State: {session_state.state.value} | Waiting {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    
    logger.info("✅ Live trader stopped")

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    # Set dry_run=False for real trading
    main(dry_run=True)
