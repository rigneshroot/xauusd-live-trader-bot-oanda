"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Stateful entry detector for live trading.
Processes candles one at a time without lookahead.
"""

import logging
from config import SKIP_FIRST_N, FVG_LOOKBACK, RETEST_PCT

logger = logging.getLogger(__name__)


class EntryDetector:
    """
    Stateful entry detection system.
    Processes candles incrementally without forward indexing.
    
    Implements two entry models:
    - Model 1: Breakout -> Retest -> Displacement confirmation
    - Model 2: Breakout -> FVG (Fair Value Gap) pattern
    """
    
    def __init__(self):
        self.reset()
        logger.info("EntryDetector initialized")
    
    def reset(self):
        """Reset all state for new session."""
        # Breakout tracking
        self.breakout_seen = False
        self.breakout_direction = None  # 'long' or 'short'
        self.breakout_time = None
        self.breakout_candle = None
        
        # Retest tracking
        self.retest_active = False
        self.retest_candle = None
        self.retest_start_idx = None
        
        # Confirmation tracking
        self.confirmed = False
        self.invalidated = False
        
        # Entry signal
        self.entry_signal = None
        self.signal_delivered = False  # Track if signal was returned to caller
        
        # Candle history (for FVG detection)
        self.candle_history = []
        self.candles_since_or_lock = 0
        
        # OR range
        self.or_high = None
        self.or_low = None
        self.or_range = None
        
        logger.debug("EntryDetector state reset")
    
    def _reset_after_invalidation(self):
        """Partial reset after invalidation to search for new breakouts."""
        logger.info("Resetting detector to search for new breakout...")
        
        # Reset breakout/retest state
        self.breakout_seen = False
        self.breakout_direction = None
        self.breakout_time = None
        self.breakout_candle = None
        self.retest_active = False
        self.retest_candle = None
        self.retest_start_idx = None
        
        # Clear invalidation flag
        self.invalidated = False
        self.confirmed = False
        self.entry_signal = None
        self.signal_delivered = False
        
        # Keep: candle_history, candles_since_or_lock, OR range
        # This allows us to continue monitoring without losing context
    
    def process_candle(self, candle, or_high, or_low):
        """
        Process a single candle and update internal state.
        
        Args:
            candle (Candle): New 1-minute candle
            or_high (float): Opening Range high
            or_low (float): Opening Range low
            
        Returns:
            dict or None: Entry signal if confirmed, None otherwise
        """
        # Always update OR range (in case it changes during OR building period)
        # This prevents using stale OR values if range updates
        if self.or_high is None:
            logger.debug(f"OR range initialized: {or_high:.2f} - {or_low:.2f}")
        self.or_high = or_high
        self.or_low = or_low
        self.or_range = or_high - or_low
        
        # Add to history (limit to 50 candles to prevent memory growth)
        self.candle_history.append(candle)
        if len(self.candle_history) > 50:
            self.candle_history.pop(0)
        
        self.candles_since_or_lock += 1
        
        # Skip first N candles after OR lock
        if self.candles_since_or_lock <= SKIP_FIRST_N:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Skipping candle {self.candles_since_or_lock}/{SKIP_FIRST_N}")
            return None
        
        # If already confirmed or invalidated, return signal only once
        if self.confirmed or self.invalidated:
            if self.signal_delivered:
                # Signal already returned, don't return it again
                return None
            else:
                # First time returning signal, mark as delivered
                self.signal_delivered = True
                return self.entry_signal
        
        # State machine processing
        if not self.breakout_seen:
            self._check_for_breakout(candle)
        
        elif self.breakout_seen and not self.retest_active:
            self._check_for_retest(candle)
        
        elif self.retest_active and not self.confirmed:
            self._check_for_confirmation(candle)
        
        # If no retest found after enough candles, try Model 2 (FVG)
        if (self.breakout_seen and 
            not self.retest_active and 
            not self.confirmed and
            len(self.candle_history) >= self.breakout_candle['index'] + 10):
            self._check_for_fvg()
        
        return self.entry_signal
    
    def _check_for_breakout(self, candle):
        """Check if candle breaks out of OR."""
        close = candle.close
        
        # Long breakout
        if close > self.or_high:
            self.breakout_seen = True
            self.breakout_direction = 'long'
            self.breakout_time = candle.timestamp
            self.breakout_candle = {
                'candle': candle,
                'index': len(self.candle_history) - 1
            }
            logger.info(f"BREAKOUT LONG detected at {candle.timestamp} | Close: {close:.2f}")
        
        # Short breakout
        elif close < self.or_low:
            self.breakout_seen = True
            self.breakout_direction = 'short'
            self.breakout_time = candle.timestamp
            self.breakout_candle = {
                'candle': candle,
                'index': len(self.candle_history) - 1
            }
            logger.info(f"BREAKOUT SHORT detected at {candle.timestamp} | Close: {close:.2f}")
    
    def _check_for_retest(self, candle):
        """Check if price retests OR boundary."""
        # Calculate retest band
        tol = self.or_range * RETEST_PCT
        anchor = self.or_high if self.breakout_direction == 'long' else self.or_low
        
        band_low = anchor - tol
        band_high = anchor + tol
        
        # Check for invalidation (re-entering OR)
        if self.breakout_direction == 'long' and candle.close < self.or_high:
            logger.info(f"INVALIDATED: Long breakout re-entered OR at {candle.timestamp}")
            self._reset_after_invalidation()
            return
        
        if self.breakout_direction == 'short' and candle.close > self.or_low:
            logger.info(f"INVALIDATED: Short breakout re-entered OR at {candle.timestamp}")
            self._reset_after_invalidation()
            return
        
        # Check if candle enters retest band
        if self.breakout_direction == 'long':
            entered_zone = (candle.low <= band_high) and (candle.high >= band_low)
        else:
            entered_zone = (candle.high >= band_low) and (candle.low <= band_high)
        
        if entered_zone:
            self.retest_active = True
            self.retest_candle = candle
            self.retest_start_idx = len(self.candle_history) - 1
            logger.info(f"RETEST detected at {candle.timestamp} | Band: {band_low:.2f}-{band_high:.2f}")
    
    def _check_for_confirmation(self, candle):
        """Check for displacement confirmation after retest."""
        if self.retest_candle is None:
            return
        
        # Calculate retest band
        tol = self.or_range * RETEST_PCT
        anchor = self.or_high if self.breakout_direction == 'long' else self.or_low
        
        band_low = anchor - tol
        band_high = anchor + tol
        
        # Check for invalidation (breaking wrong side of band)
        if self.breakout_direction == 'long' and candle.low < band_low:
            logger.info(f"INVALIDATED: Broke below retest band at {candle.timestamp}")
            self._reset_after_invalidation()
            return
        
        if self.breakout_direction == 'short' and candle.high > band_high:
            logger.info(f"INVALIDATED: Broke above retest band at {candle.timestamp}")
            self._reset_after_invalidation()
            return
        
        # Get previous candle
        if len(self.candle_history) < 2:
            return
        
        prev_candle = self.candle_history[-2]
        
        # Calculate consolidation zone
        cons_low = self.retest_candle.low - tol
        cons_high = self.retest_candle.high + tol
        
        # Calculate body ratio
        body_size = abs(candle.close - candle.open)
        full_range = max(candle.high - candle.low, 0.0001)
        body_ratio = body_size / full_range
        
        # Check for displacement
        displacement = False
        
        if self.breakout_direction == 'long':
            displacement = (
                candle.close > cons_high and
                candle.close > prev_candle.close and
                candle.high > prev_candle.high and
                body_ratio >= 0.30
            )
            
            # Also check for FVG
            if len(self.candle_history) >= 3:
                c1 = self.candle_history[-3]
                c3 = candle
                fvg = (c1.high < c3.low)
                displacement = displacement or fvg
        
        else:  # short
            displacement = (
                candle.close < cons_low and
                candle.close < prev_candle.close and
                candle.low < prev_candle.low and
                body_ratio >= 0.30
            )
            
            # Also check for FVG
            if len(self.candle_history) >= 3:
                c1 = self.candle_history[-3]
                c3 = candle
                fvg = (c1.low > c3.high)
                displacement = displacement or fvg
        
        if displacement:
            self.confirmed = True
            self._generate_entry_signal(candle, model=1)
            logger.info(f"CONFIRMED Model 1 at {candle.timestamp} | Entry: {candle.close:.2f}")
    
    def _check_for_fvg(self):
        """Check for Fair Value Gap pattern (Model 2)."""
        if len(self.candle_history) < FVG_LOOKBACK:
            return
        
        # Search for FVG from breakout onwards (limit to last 20 candles for performance)
        start_idx = self.breakout_candle['index']
        search_start = max(start_idx, len(self.candle_history) - 20)
        
        for i in range(search_start, len(self.candle_history) - FVG_LOOKBACK + 1):
            block = self.candle_history[i:i + FVG_LOOKBACK]
            
            if self.breakout_direction == 'long':
                # Check if first candle high < last candle low (gap)
                if block[0].high < block[-1].low:
                    self.confirmed = True
                    entry_candle = block[-1]
                    self._generate_entry_signal(entry_candle, model=2)
                    logger.info(f"CONFIRMED Model 2 (FVG) at {entry_candle.timestamp} | Entry: {entry_candle.close:.2f}")
                    return
            
            else:  # short
                # Check if first candle low > last candle high (gap)
                if block[0].low > block[-1].high:
                    self.confirmed = True
                    entry_candle = block[-1]
                    self._generate_entry_signal(entry_candle, model=2)
                    logger.info(f"CONFIRMED Model 2 (FVG) at {entry_candle.timestamp} | Entry: {entry_candle.close:.2f}")
                    return
    
    def _generate_entry_signal(self, candle, model):
        """
        Generate entry signal with SL and TP.
        
        Args:
            candle (Candle): Entry candle
            model (int): Entry model (1 or 2)
        """
        entry_price = candle.close
        
        # Calculate SL and TP
        if model == 1 and self.retest_candle is not None:
            # Model 1: Use retest structure for SL
            if self.breakout_direction == 'long':
                sl = self.retest_candle.low
                if sl >= entry_price:  # Safety fallback
                    sl = entry_price - 0.50
                sl_dist = entry_price - sl
                tp = entry_price + (2 * sl_dist)
            else:  # short
                sl = self.retest_candle.high
                if sl <= entry_price:  # Safety fallback
                    sl = entry_price + 0.50
                sl_dist = sl - entry_price
                tp = entry_price - (2 * sl_dist)
        
        else:
            # Model 2 or fallback: Use ATR-based SL
            # Calculate simple ATR from recent candles
            recent = self.candle_history[-14:] if len(self.candle_history) >= 14 else self.candle_history
            atr = sum(c.high - c.low for c in recent) / len(recent)
            sl_dist = 0.8 * atr
            
            if self.breakout_direction == 'long':
                sl = entry_price - sl_dist
                tp = entry_price + (2 * sl_dist)
            else:  # short
                sl = entry_price + sl_dist
                tp = entry_price - (2 * sl_dist)
        
        self.entry_signal = {
            'model': model,
            'direction': self.breakout_direction,
            'entry_time': candle.timestamp,
            'entry_price': entry_price,
            'sl': sl,
            'tp': tp,
            'breakout_time': self.breakout_time,
            'retest_time': self.retest_candle.timestamp if self.retest_candle else None
        }
    
    def get_signal(self):
        """
        Get entry signal if confirmed.
        
        Returns:
            dict or None: Entry signal or None
        """
        return self.entry_signal
    
    def is_invalidated(self):
        """Check if current setup is invalidated."""
        return self.invalidated
