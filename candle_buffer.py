"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Rolling candle buffer for live trading system.
Maintains 1-minute and 5-minute candles without full DataFrame overhead.
"""

import datetime
import pytz
from collections import deque
from threading import Lock
import logging

from config import MAX_1M_CANDLES, MAX_5M_CANDLES

logger = logging.getLogger(__name__)


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
    
    def to_dict(self):
        """Convert to dictionary format."""
        return {
            't': self.timestamp,
            'o': self.open,
            'h': self.high,
            'l': self.low,
            'c': self.close,
            'v': self.volume
        }


class CandleBuffer:
    """
    Thread-safe rolling buffer for 1-minute and 5-minute candles.
    Aggregates ticks into 1m candles and builds 5m candles from 1m data.
    """
    
    def __init__(self):
        self.candles_1m = deque(maxlen=MAX_1M_CANDLES)
        self.candles_5m = deque(maxlen=MAX_5M_CANDLES)
        self.lock = Lock()
        
        # Current 1-minute candle being built
        self.current_candle = None
        self.current_minute = None
        
        # Cache timezone object (optimization: avoid recreating on every tick)
        self.ny_tz = pytz.timezone('America/New_York')
        
        logger.info("CandleBuffer initialized")
    
    def add_tick(self, timestamp, bid, ask):
        """
        Add a tick and aggregate into 1-minute candles.
        
        Args:
            timestamp (datetime): Tick timestamp (UTC)
            bid (float): Bid price
            ask (float): Ask price
        """
        with self.lock:
            # Use mid price
            mid = (bid + ask) / 2.0
            
            # Convert to NY timezone for candle alignment
            ny_time = timestamp.astimezone(self.ny_tz)
            
            # Round down to minute
            candle_minute = ny_time.replace(second=0, microsecond=0)
            
            # Check if we're starting a new candle
            if self.current_minute is None or candle_minute > self.current_minute:
                # Close previous candle if exists
                if self.current_candle is not None:
                    self._close_1m_candle()
                
                # Start new candle
                self.current_minute = candle_minute
                self.current_candle = {
                    'timestamp': candle_minute,
                    'open': mid,
                    'high': mid,
                    'low': mid,
                    'close': mid,
                    'volume': 1
                }
            else:
                # Update current candle
                self.current_candle['high'] = max(self.current_candle['high'], mid)
                self.current_candle['low'] = min(self.current_candle['low'], mid)
                self.current_candle['close'] = mid
                self.current_candle['volume'] += 1
    
    def _close_1m_candle(self):
        """Close the current 1-minute candle and add to buffer."""
        if self.current_candle is None:
            return
        
        candle = Candle(
            timestamp=self.current_candle['timestamp'],
            open_price=self.current_candle['open'],
            high=self.current_candle['high'],
            low=self.current_candle['low'],
            close=self.current_candle['close'],
            volume=self.current_candle['volume']
        )
        
        self.candles_1m.append(candle)
        
        # Optimization: only format debug string if debug logging enabled
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"1m candle closed: {candle}")
        
        # Update 5m candles
        self._update_5m_candles()
    
    def _update_5m_candles(self):
        """Build 5-minute candles from 1-minute data."""
        if len(self.candles_1m) < 5:
            return
        
        # Get last candle timestamp
        last_1m = self.candles_1m[-1]
        last_minute = last_1m.timestamp.minute
        
        # Check if we just completed a 5-minute period
        # We want to build a 5m candle when we have 5 consecutive 1m candles
        # For OR: 09:30, 09:31, 09:32, 09:33, 09:34 -> build at 09:34
        if last_minute % 5 == 4:  # Minutes ending in 4 or 9 (09:34, 09:39, 09:44, etc.)
            # Get last 5 candles
            recent_5 = list(self.candles_1m)[-5:]
            
            # Verify they are consecutive (all within same 5-minute period)
            first_minute = recent_5[0].timestamp.minute
            if first_minute % 5 == 0:  # Should start at 0 or 5 (09:30, 09:35, etc.)
                # Build 5m candle
                candle_5m = Candle(
                    timestamp=recent_5[0].timestamp,  # Start time of 5m period
                    open_price=recent_5[0].open,
                    high=max(c.high for c in recent_5),
                    low=min(c.low for c in recent_5),
                    close=recent_5[-1].close,
                    volume=sum(c.volume for c in recent_5)
                )
                
                self.candles_5m.append(candle_5m)
                
                # Optimization: only format debug string if debug logging enabled
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"5m candle built: {candle_5m}")
    
    def get_latest_1m(self, n=1):
        """
        Get the last N 1-minute candles.
        
        Args:
            n (int): Number of candles to retrieve
            
        Returns:
            list: List of Candle objects (oldest to newest)
        """
        with self.lock:
            if n > len(self.candles_1m):
                n = len(self.candles_1m)
            return list(self.candles_1m)[-n:] if n > 0 else []
    
    def get_latest_5m(self, n=1):
        """
        Get the last N 5-minute candles.
        
        Args:
            n (int): Number of candles to retrieve
            
        Returns:
            list: List of Candle objects (oldest to newest)
        """
        with self.lock:
            if n > len(self.candles_5m):
                n = len(self.candles_5m)
            return list(self.candles_5m)[-n:] if n > 0 else []
    
    def get_or_candles(self, date=None):
        """
        Get Opening Range candles (09:30-09:34 NY time).
        
        Args:
            date (datetime.date): Date to get OR for (default: today)
            
        Returns:
            list: List of 5m candles in OR period
        """
        with self.lock:
            if date is None:
                ny_tz = pytz.timezone('America/New_York')
                date = datetime.datetime.now(ny_tz).date()
            
            or_candles = []
            for candle in self.candles_5m:
                candle_date = candle.timestamp.date()
                candle_time = candle.timestamp.time()
                
                # Check if candle is in OR period (09:30-09:34)
                if (candle_date == date and 
                    datetime.time(9, 30) <= candle_time <= datetime.time(9, 34)):
                    or_candles.append(candle)
            
            return or_candles
    
    def has_new_candle(self):
        """
        Check if a new 1-minute candle was just closed.
        
        Returns:
            bool: True if new candle available
        """
        with self.lock:
            return len(self.candles_1m) > 0
    
    def clear(self):
        """Clear all candles from buffer."""
        with self.lock:
            self.candles_1m.clear()
            self.candles_5m.clear()
            self.current_candle = None
            self.current_minute = None
            logger.info("CandleBuffer cleared")
