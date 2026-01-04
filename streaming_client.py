"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
OANDA streaming price client.
Connects to OANDA streaming API and publishes real-time ticks.
"""

import oandapyV20
from oandapyV20.endpoints import pricing
import logging
import time
from threading import Thread, Event

from config import OANDA_ACCESS_TOKEN, OANDA_ACCOUNT_ID, INSTRUMENT

logger = logging.getLogger(__name__)


class StreamingClient:
    """
    OANDA streaming price client.
    Subscribes to real-time prices and publishes ticks to callback.
    """
    
    def __init__(self, on_tick_callback):
        """
        Initialize streaming client.
        
        Args:
            on_tick_callback (callable): Function to call with each tick
                                        Signature: on_tick_callback(timestamp, bid, ask)
        """
        self.client = oandapyV20.API(access_token=OANDA_ACCESS_TOKEN)
        self.account_id = OANDA_ACCOUNT_ID
        self.instrument = INSTRUMENT
        self.on_tick_callback = on_tick_callback
        
        self.running = False
        self.stop_event = Event()
        self.stream_thread = None
        
        logger.info(f"StreamingClient initialized for {INSTRUMENT}")
    
    def start(self):
        """Start streaming in background thread."""
        if self.running:
            logger.warning("StreamingClient already running")
            return
        
        self.running = True
        self.stop_event.clear()
        self.stream_thread = Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        logger.info("StreamingClient started")
    
    def stop(self):
        """Stop streaming."""
        if not self.running:
            return
        
        logger.info("Stopping StreamingClient...")
        self.running = False
        self.stop_event.set()
        
        if self.stream_thread:
            self.stream_thread.join(timeout=5)
        
        logger.info("StreamingClient stopped")
    
    def _stream_loop(self):
        """Main streaming loop (runs in background thread)."""
        while self.running:
            try:
                self._connect_and_stream()
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                if self.running:
                    logger.info("Reconnecting in 5 seconds...")
                    time.sleep(5)
    
    def _connect_and_stream(self):
        """Connect to OANDA and process stream."""
        params = {
            "instruments": self.instrument
        }
        
        r = pricing.PricingStream(accountID=self.account_id, params=params)
        
        logger.info(f"Connecting to OANDA stream for {self.instrument}...")
        
        try:
            # OANDA API returns messages directly (not as tuples)
            for msg in self.client.request(r):
                if self.stop_event.is_set():
                    break
                
                # Check message type
                msg_type = msg.get('type', '')
                
                # Process price messages
                if msg_type == 'PRICE':
                    self._process_price(msg)
                
        except Exception as e:
            if self.running:
                raise e
    
    def _process_price(self, price_msg):
        """
        Process a price message from the stream.
        
        Args:
            price_msg (dict): Price message from OANDA
        """
        try:
            # Extract price data
            timestamp = price_msg.get('time')
            
            # Get bid/ask prices
            bids = price_msg.get('bids', [])
            asks = price_msg.get('asks', [])
            
            if not bids or not asks:
                return
            
            bid = float(bids[0]['price'])
            ask = float(asks[0]['price'])
            
            # Parse timestamp
            from datetime import datetime
            import pytz
            
            # OANDA timestamps are in RFC3339 format with nanosecond precision
            # Python's fromisoformat only handles up to microseconds
            # Truncate to microseconds: '2026-01-02T21:59:05.222899102+00:00' -> '2026-01-02T21:59:05.222899+00:00'
            if '.' in timestamp:
                parts = timestamp.split('.')
                # Keep only first 6 digits after decimal (microseconds)
                fractional = parts[1][:6]
                timezone_part = parts[1][parts[1].find('+'):]  # Get +00:00 part
                timestamp = f"{parts[0]}.{fractional}{timezone_part}"
            
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Call the callback with tick data
            self.on_tick_callback(ts, bid, ask)
            
        except Exception as e:
            logger.error(f"Error processing price: {e}")
    
    def is_running(self):
        """Check if streaming is active."""
        return self.running
