"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Session state machine for live trading.
Manages trading session states and Opening Range detection.
"""

import datetime
import logging
from enum import Enum

from utils import get_ny_time
from config import SESSION_START, OR_LOCK_TIME, SESSION_END, ENABLE_OR_FILTER, MIN_OR_RANGE, MAX_OR_RANGE

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Trading session states."""
    PRE_OR = "PRE_OR"  # Before 09:30 NY
    OR_BUILDING = "OR_BUILDING"  # 09:30-09:34 NY, collecting OR candles
    OR_LOCKED = "OR_LOCKED"  # 09:35 NY, OR range finalized
    POST_OR_TRADING = "POST_OR_TRADING"  # After 09:35, monitoring for entries
    SESSION_CLOSED = "SESSION_CLOSED"  # Trade taken or after 16:00


class SessionStateMachine:
    """
    Manages trading session lifecycle and Opening Range detection.
    Enforces one trade per session.
    """
    
    def __init__(self):
        self.state = SessionState.PRE_OR
        self.or_high = None
        self.or_low = None
        self.or_open_time = None
        self.or_close_time = None
        self.trade_taken = False
        self.current_date = None
        
        logger.info("SessionStateMachine initialized in PRE_OR state")
    
    def update(self, candle_buffer):
        """
        Update state machine based on current time and candle data.
        
        Args:
            candle_buffer (CandleBuffer): Buffer containing candles
        """
        ny_time = get_ny_time()
        current_time = ny_time.time()
        current_date = ny_time.date()
        
        # Reset state machine for new day
        if self.current_date != current_date:
            self._reset_for_new_day(current_date)
        
        # State transitions
        if self.state == SessionState.PRE_OR:
            self._handle_pre_or(current_time)
        
        elif self.state == SessionState.OR_BUILDING:
            self._handle_or_building(current_time, candle_buffer)
        
        elif self.state == SessionState.OR_LOCKED:
            self._handle_or_locked()
        
        elif self.state == SessionState.POST_OR_TRADING:
            self._handle_post_or_trading(current_time)
    
    def _reset_for_new_day(self, new_date):
        """Reset state for a new trading day."""
        logger.info(f"Resetting state machine for new day: {new_date}")
        self.state = SessionState.PRE_OR
        self.or_high = None
        self.or_low = None
        self.or_open_time = None
        self.or_close_time = None
        self.trade_taken = False
        self.current_date = new_date
    
    def _handle_pre_or(self, current_time):
        """Handle PRE_OR state - waiting for session start."""
        session_start = datetime.time(9, 30)
        
        if current_time >= session_start:
            self._transition_to(SessionState.OR_BUILDING)
    
    def _handle_or_building(self, current_time, candle_buffer):
        """Handle OR_BUILDING state - collecting OR candles."""
        or_lock = datetime.time(9, 35)
        
        if current_time >= or_lock:
            # Calculate OR high/low from 5m candles
            or_candles = candle_buffer.get_or_candles()
            
            if len(or_candles) > 0:
                self.or_high = max(c.high for c in or_candles)
                self.or_low = min(c.low for c in or_candles)
                self.or_open_time = or_candles[0].timestamp
                self.or_close_time = or_candles[-1].timestamp
                
                or_range = self.or_high - self.or_low
                
                # Check OR range filters
                if ENABLE_OR_FILTER:
                    if or_range < MIN_OR_RANGE:
                        logger.warning(f"OR range too small ({or_range:.2f} < {MIN_OR_RANGE}) - skipping trading today")
                        self._transition_to(SessionState.SESSION_CLOSED)
                        return
                    if or_range > MAX_OR_RANGE:
                        logger.warning(f"OR range too large ({or_range:.2f} > {MAX_OR_RANGE}) - skipping trading today")
                        self._transition_to(SessionState.SESSION_CLOSED)
                        return
                
                logger.info(f"OR LOCKED at 09:35 | High: {self.or_high:.2f} | Low: {self.or_low:.2f} | Range: {or_range:.2f}")
                self._transition_to(SessionState.OR_LOCKED)
            else:
                logger.warning("No OR candles found at 09:35, staying in OR_BUILDING")
    
    def _handle_or_locked(self):
        """Handle OR_LOCKED state - immediately transition to trading."""
        self._transition_to(SessionState.POST_OR_TRADING)
    
    def _handle_post_or_trading(self, current_time):
        """Handle POST_OR_TRADING state - check for session end."""
        session_end = datetime.time(16, 0)
        
        if current_time >= session_end:
            logger.info("Session ended at 16:00 NY time")
            self._transition_to(SessionState.SESSION_CLOSED)
    
    def _transition_to(self, new_state):
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state
        logger.info(f"State transition: {old_state.value} -> {new_state.value}")
    
    def mark_trade_taken(self):
        """Mark that a trade has been taken (one per session)."""
        self.trade_taken = True
        logger.info("Trade taken - closing session")
        self._transition_to(SessionState.SESSION_CLOSED)
    
    def can_trade(self):
        """
        Check if trading is allowed.
        
        Returns:
            bool: True if in POST_OR_TRADING state and no trade taken
        """
        return (self.state == SessionState.POST_OR_TRADING and 
                not self.trade_taken and 
                self.or_high is not None and 
                self.or_low is not None)
    
    def get_or_range(self):
        """
        Get Opening Range high and low.
        
        Returns:
            tuple: (or_high, or_low) or (None, None) if not available
        """
        return self.or_high, self.or_low
    
    def get_state_info(self):
        """
        Get current state information for logging.
        
        Returns:
            dict: State information
        """
        return {
            'state': self.state.value,
            'or_high': self.or_high,
            'or_low': self.or_low,
            'trade_taken': self.trade_taken,
            'can_trade': self.can_trade()
        }
