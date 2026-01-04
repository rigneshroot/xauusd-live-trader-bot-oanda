"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Utility functions for live trading system
"""

import datetime
import pytz
import logging
from config import LOG_FILE, LOG_LEVEL, LOG_TICK_DATA


def get_ny_time():
    """
    Get current time in New York timezone.
    
    Returns:
        datetime: Current time in America/New_York timezone
    """
    ny_tz = pytz.timezone('America/New_York')
    return datetime.datetime.now(ny_tz)


def is_market_open():
    """
    Check if market is currently open for trading.
    
    Returns:
        bool: True if within trading hours (09:30-16:00 NY time)
    """
    ny_time = get_ny_time()
    current_time = ny_time.time()
    
    # Check if weekday (Monday=0, Sunday=6)
    if ny_time.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if within trading hours
    start = datetime.time(9, 30)
    end = datetime.time(16, 0)
    
    return start <= current_time <= end


def setup_logging():
    """
    Configure logging for the live trading system.
    
    Sets up both file and console logging with appropriate formats.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger


def format_price(price):
    """
    Format price for display (2 decimal places for gold).
    
    Args:
        price (float): Price to format
        
    Returns:
        str: Formatted price string
    """
    return f"{price:.2f}"


def calculate_sl_tp(direction, entry_price, sl_price, risk_reward=2):
    """
    Calculate stop loss and take profit levels.
    
    Args:
        direction (str): 'long' or 'short'
        entry_price (float): Entry price
        sl_price (float): Stop loss price
        risk_reward (float): Risk/reward ratio (default 2)
        
    Returns:
        tuple: (sl, tp) prices
    """
    if direction == 'long':
        sl_dist = entry_price - sl_price
        tp = entry_price + (risk_reward * sl_dist)
    else:  # short
        sl_dist = sl_price - entry_price
        tp = entry_price - (risk_reward * sl_dist)
    
    return sl_price, tp


def time_until_next_session():
    """
    Calculate time until next trading session starts.
    
    Returns:
        timedelta: Time until 09:30 NY time
    """
    ny_time = get_ny_time()
    
    # If before 09:30 today, return time until 09:30 today
    session_start = ny_time.replace(hour=9, minute=30, second=0, microsecond=0)
    if ny_time.time() < datetime.time(9, 30):
        return session_start - ny_time
    
    # Otherwise, return time until 09:30 tomorrow
    next_day = ny_time + datetime.timedelta(days=1)
    next_session = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # Skip weekends
    while next_session.weekday() >= 5:
        next_session += datetime.timedelta(days=1)
    
    return next_session - ny_time
