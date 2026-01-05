# 🎓 Beginner's Guide to Live Trading System

## What This System Does

This system **automatically trades** based on the Opening Range (OR) strategy:
1. Waits for market to open at 9:30 AM NY time
2. Watches the first 5 minutes (9:30-9:34) to find high/low range
3. Waits for price to break out of that range
4. Looks for a retest (price coming back to test the breakout)
5. Enters a trade when confirmed
6. Takes **one trade per day** maximum
7. Automatically sets stop loss and take profit

## 📁 What Each File Does

### Configuration Files (You'll Edit These)

**`config.py`** - All your settings in one place
- OANDA account details
- How many units to trade (position size)
- Strategy parameters (how aggressive/conservative)

### Core Trading Files (Don't Need to Edit)

**`live_trader.py`** - The main program
- Starts everything up
- Coordinates all the other parts
- Think of it as the "brain"

**`candle_buffer.py`** - Stores price data
- Keeps track of recent candles (like a rolling window)
- Builds 1-minute and 5-minute candles from live prices

**`session_state.py`** - Tracks what phase we're in
- Before market open
- Building the Opening Range (9:30-9:34)
- Looking for trades (after 9:35)
- Done for the day

**`entry_detector.py`** - Finds trade opportunities
- Watches for breakouts
- Looks for retests
- Confirms entry signals

**`oanda_executor.py`** - Places actual trades
- Sends orders to OANDA
- Attaches stop loss and take profit
- Monitors your position

**`streaming_client.py`** - Gets live prices
- Connects to OANDA's price stream
- Receives real-time price updates

**`utils.py`** - Helper functions
- Time zone handling
- Logging setup
- Small utility functions

### Special Files

**`live_trader_colab.py`** - Google Colab version
- Single file with everything combined
- Uses polling instead of streaming
- Perfect for running in a notebook

**`emergency_close.py`** - Emergency stop
- Closes all positions immediately
- Use if something goes wrong

## 🚀 Quick Start (Absolute Beginner)

### Step 1: Install Python Packages

Open Terminal and run:
```bash
cd /xauusd-live-trader-bot-oanda
pip3 install oandapyV20 pandas pytz
```

### Step 2: Check Your Settings

Open `config.py` and verify:
```python
OANDA_ACCOUNT_ID = '101-001-28669650-002'  # Your account
UNITS = 3  # How many units to trade (start small!)
```

### Step 3: Test Without Real Money

```bash
python3 live_trader.py --dry-run
```

This will:
- ✅ Connect to OANDA
- ✅ Get live prices
- ✅ Detect entry signals
- ❌ NOT place real orders (just logs them)

### Step 4: Watch It Run

Open another Terminal window and watch the logs:
```bash
cd /Users/subramanyaacharpadamanur/Documents/ScalpingStrategyOANDA
tail -f live_trader.log
```

You'll see messages like:
- `State transition: PRE_OR -> OR_BUILDING` (Market opened)
- `OR LOCKED | High: 2645.50 | Low: 2643.20` (Range found)
- `BREAKOUT LONG detected` (Price broke out)
- `ENTRY SIGNAL DETECTED!` (Trade opportunity found)

### Step 5: Stop the System

Press `Ctrl+C` in the Terminal where it's running.

## ⚙️ Understanding config.py

```python
# Your OANDA account details
OANDA_ACCOUNT_ID = '101-001-28669650-002'  # Don't change
OANDA_ACCESS_TOKEN = '...'  # Don't change

# What to trade
INSTRUMENT = 'XAU_USD'  # Gold (don't change unless you know what you're doing)

# Position size
UNITS = 3  # Start with 3, increase when confident
           # Each unit = $1 per point movement

# Risk/Reward ratio
RISK_REWARD = 2  # Take profit is 2x your stop loss
                 # Example: Risk $50 to make $100

# Strategy tuning (advanced - don't change initially)
SKIP_FIRST_N = 5  # Skip first 5 candles after OR
FVG_LOOKBACK = 3  # How many candles to check for gaps
RETEST_PCT = 0.05  # How close to OR counts as retest (5%)
```

## 🎯 What to Expect

### Normal Day Timeline

**9:25 AM** - Start the system
```bash
python3 live_trader.py --dry-run
```

**9:30 AM** - Market opens, system starts watching

**9:35 AM** - Opening Range locked
```
OR LOCKED | High: 2645.50 | Low: 2643.20
```

**9:40-11:00 AM** - Looking for entry
- May see breakouts
- May see retests
- May get entry signal

**When Signal Appears**
```
📊 ENTRY SIGNAL DETECTED!
   Model: 1
   Direction: LONG
   Entry: 2646.80
   SL: 2645.20
   TP: 2650.00
```

**After Trade** - System closes for the day

### What If Nothing Happens?

That's normal! Not every day has a valid setup:
- No breakout = No trade
- Breakout but no retest = No trade (usually)
- Retest but no confirmation = No trade

**This is good!** The system is protecting you from bad trades.

## 🛡️ Safety Features

### 1. Dry-Run Mode
Always test first:
```bash
python3 live_trader.py --dry-run
```

### 2. One Trade Per Day
Can't overtrade - system stops after one trade

### 3. Automatic Stop Loss
Every trade has a stop loss (limits losses)

### 4. Automatic Take Profit
Every trade has a take profit (locks in gains)

### 5. Emergency Stop
If something goes wrong:
```bash
python3 emergency_close.py
```

## 📊 Reading the Logs

### Good Signs ✅
```
State transition: PRE_OR -> OR_BUILDING
OR LOCKED | High: 2645.50 | Low: 2643.20
BREAKOUT LONG detected
RETEST detected
CONFIRMED Model 1
Order placed successfully!
```

### Warning Signs ⚠️
```
INVALIDATED: Long breakout re-entered OR
No entry (no retest & no FVG)
```
These are normal - the system is being cautious

### Error Signs ❌
```
Error in event loop
Order placement failed
Connection timeout
```
These need attention - check your internet and OANDA account

## 🔧 Common Adjustments

### Make It More Conservative
```python
# In config.py
SKIP_FIRST_N = 10  # Wait longer after OR
RETEST_PCT = 0.03  # Stricter retest requirement (3%)
```

### Make It More Aggressive
```python
# In config.py
SKIP_FIRST_N = 3  # Enter sooner
RETEST_PCT = 0.08  # Looser retest requirement (8%)
```

### Change Position Size
```python
# In config.py
UNITS = 1  # Very conservative
UNITS = 3  # Moderate (default)
UNITS = 5  # Aggressive (only if confident!)
```

## ❓ FAQ

### Q: Do I need to keep my computer on all day?
**A:** Yes, or use Oracle Cloud (see ORACLE_QUICKSTART.md)

### Q: What if I miss the 9:30 start?
**A:** Start it anytime before 9:35. After 9:35, wait for next day.

### Q: Can I run multiple instruments?
**A:** Not with this setup. One instrument = one instance.

### Q: How do I know it's working?
**A:** Watch the logs. You should see state transitions and price updates.

### Q: What if it doesn't find any trades?
**A:** That's normal and good! It's being selective.

### Q: Can I backtest changes?
**A:** Yes! Use `scalping_strategy_works.py` for backtesting.

## 🎓 Learning Path

### Week 1: Observation
- Run in dry-run mode
- Watch the logs
- Understand the state transitions
- See how it detects entries

### Week 2: Paper Trading
- Still dry-run, but track results
- Compare with backtesting
- Build confidence

### Week 3: Small Live Trading
- Start with UNITS = 1
- One trade per day
- Monitor closely

### Week 4+: Scale Up
- Increase position size gradually
- Keep detailed records
- Refine parameters based on results

## 🆘 Getting Help

### Check Logs First
```bash
tail -n 100 live_trader.log
```

### Test Connection
```bash
python3 -c "import oandapyV20; print('OK')"
```

### Verify Settings
```bash
python3 -c "from config import *; print(f'Account: {OANDA_ACCOUNT_ID}, Units: {UNITS}')"
```

### Common Fixes

**"Module not found"**
```bash
pip3 install oandapyV20 pandas pytz
```

**"Connection refused"**
- Check internet connection
- Verify OANDA API credentials
- Check if OANDA is having issues

**"No module named 'config'"**
```bash
# Make sure you're in the right directory
cd /Users/subramanyaacharpadamanur/Documents/ScalpingStrategyOANDA
```

## 📚 Next Steps

1. Read through `config.py` - understand each setting
2. Run in dry-run mode for a week
3. Read the logs daily
4. Compare with your backtesting results
5. When confident, try paper trading
6. Only go live when you're 100% comfortable

Remember: **There's no rush!** Take your time to understand the system before risking real money.
