"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Configuration template for live trading system

INSTRUCTIONS:
1. Copy this file to config.py
2. Fill in your OANDA credentials
3. Adjust trading parameters as needed
4. NEVER commit config.py to Git (it's in .gitignore)
"""

# ============================================================================
# OANDA API CREDENTIALS (REQUIRED - Fill these in!)
# ============================================================================
OANDA_ACCOUNT_ID = 'YOUR_ACCOUNT_ID_HERE'  # Example: '101-001-12345678-001'
OANDA_ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN_HERE'  # Get from OANDA dashboard

# ============================================================================
# TRADING PARAMETERS (You can adjust these)
# ============================================================================

# What instrument to trade
INSTRUMENT = 'XAU_USD'  # Gold vs US Dollar
                        # Don't change unless you know other instruments

# Position size (START HERE!)
UNITS = 3  # How many units to trade
           # 1 unit = ~$1 per point movement
           # BEGINNER: Start with 1, increase to 3 after a week
           # INTERMEDIATE: 3-5 units
           # ADVANCED: 5-10 units

# Risk/Reward ratio
RISK_REWARD = 2  # Take profit is 2x your stop loss
                 # Example: Risk $50 to potentially make $100
                 # BEGINNER: Keep at 2
                 # ADVANCED: Try 1.5 (more conservative) or 3 (more aggressive)

# ============================================================================
# STRATEGY PARAMETERS (Advanced - don't change initially)
# ============================================================================

# Skip first N candles after Opening Range locks
SKIP_FIRST_N = 5  # Wait 5 minutes after 9:35 before looking for entries
                  # CONSERVATIVE: 10 (wait longer, fewer trades)
                  # DEFAULT: 5 (balanced)
                  # AGGRESSIVE: 3 (enter sooner, more trades)

# Fair Value Gap (FVG) detection
FVG_LOOKBACK = 3  # How many candles to check for price gaps
                  # Don't change unless you understand FVG patterns

# Retest tolerance
RETEST_PCT = 0.05  # How close to OR boundary counts as a "retest"
                   # 0.05 = 5% of the OR range
                   # STRICT: 0.03 (3% - fewer but higher quality setups)
                   # DEFAULT: 0.05 (5% - balanced)
                   # LOOSE: 0.08 (8% - more setups but lower quality)

# ============================================================================
# MARKET CONDITION FILTERS
# ============================================================================

# Maximum invalidation resets per session
MAX_INVALIDATIONS = 2  # Stop after 2 failed attempts (CONSERVATIVE)
                       # Based on analysis: avg 2.5 invalidations/session
                       # CONSERVATIVE: 2 (recommended - would have avoided recent losses)
                       # BALANCED: 3
                       # AGGRESSIVE: 5

# Opening Range size filters
ENABLE_OR_FILTER = True  # Enable OR range filtering
MIN_OR_RANGE = 12.0  # Minimum OR range in points (CONSERVATIVE)
                     # Based on analysis: recent sessions had ~11.4 points
                     # CONSERVATIVE: 12.0 (would have skipped recent losses)
                     # BALANCED: 8.0
                     # AGGRESSIVE: 5.0
MAX_OR_RANGE = 18.0  # Maximum OR range in points
                     # CONSERVATIVE: 18.0
                     # BALANCED: 20.0
                     # AGGRESSIVE: 25.0

# Time-based entry filter
MIN_ENTRY_TIME = '10:00'  # Don't enter before this time (NY timezone)
                          # Avoids early false signals
                          # CONSERVATIVE: '10:00' (would have avoided Jan 8 loss)
                          # BALANCED: '09:50'
                          # AGGRESSIVE: '09:40'

# Stop Loss buffer
SL_BUFFER_PCT = 0.5  # SL buffer as percentage of OR range
                     # Prevents tight SLs in volatile conditions
                     # CONSERVATIVE: 0.5 (50% of OR range)
                     # BALANCED: 0.3 (30% of OR range)
                     # AGGRESSIVE: 0.2 (20% of OR range)

# ============================================================================
# SESSION TIMES (New York timezone - don't change)
# ============================================================================
SESSION_START = '09:30'  # Market open
OR_LOCK_TIME = '09:35'  # Opening Range lock time
SESSION_END = '16:00'  # End of trading session

# ============================================================================
# BUFFER SIZES (Advanced - don't change)
# ============================================================================
MAX_1M_CANDLES = 500  # Keep last 500 1-minute candles
MAX_5M_CANDLES = 100  # Keep last 100 5-minute candles

# ============================================================================
# LOGGING (Advanced - don't change)
# ============================================================================
LOG_FILE = 'live_trader.log'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
