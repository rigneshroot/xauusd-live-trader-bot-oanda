# 🎯 Quick Reference Card

## Starting the System

### Easiest Way (Recommended for Beginners)
```bash
./start_trading.sh
```
Then choose option 1 for practice mode.

### Manual Way
```bash
# Practice mode (no real orders)
python3 live_trader.py --dry-run

# Live trading (real orders!)
python3 live_trader.py
```

## Stopping the System

Press `Ctrl+C` in the terminal where it's running.

## Watching Logs

```bash
tail -f live_trader.log
```

## Emergency Stop

```bash
python3 emergency_close.py
```

## Key Settings (config.py)

| Setting | What It Does | Beginner Value |
|---------|--------------|----------------|
| `UNITS` | Position size | Start with `1` |
| `RISK_REWARD` | TP vs SL ratio | Keep at `2` |
| `SKIP_FIRST_N` | Wait time after OR | Keep at `5` |
| `RETEST_PCT` | Retest strictness | Keep at `0.05` |

## What to Watch For

### ✅ Good Signs
- `State transition: PRE_OR -> OR_BUILDING`
- `OR LOCKED | High: X | Low: Y`
- `BREAKOUT LONG/SHORT detected`
- `ENTRY SIGNAL DETECTED!`
- `Order placed successfully!`

### ⚠️ Normal (Not Bad)
- `INVALIDATED: ...` (Setup didn't work out)
- `No entry (no retest & no FVG)` (No valid setup today)

### ❌ Problems
- `Error in event loop`
- `Order placement failed`
- `Connection timeout`

## Daily Routine

### Morning (Before 9:30 AM)
1. Open Terminal
2. Run `./start_trading.sh`
3. Choose option 1 (dry-run) or 2 (live)
4. Open another Terminal
5. Run `tail -f live_trader.log`

### During Trading (9:30 AM - 4:00 PM)
- Watch the logs
- Don't interfere unless there's an error
- System handles everything automatically

### Evening (After 4:00 PM)
- Press `Ctrl+C` to stop
- Review the logs
- Check if any trades were taken

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Module not found" | Run: `pip3 install oandapyV20 pandas pytz` |
| "Connection refused" | Check internet, verify OANDA credentials |
| "No such file" | Make sure you're in the right directory |
| System won't start | Check logs: `cat live_trader.log` |

## Files You'll Use

| File | When to Use It |
|------|----------------|
| `start_trading.sh` | Every day to start |
| `config.py` | To change settings |
| `live_trader.log` | To see what's happening |
| `emergency_close.py` | Only in emergencies |
| `BEGINNERS_GUIDE.md` | When you have questions |

## Important Reminders

1. **Always start with dry-run** for at least a week
2. **One trade per day maximum** (system enforces this)
3. **Don't change settings mid-session** (restart required)
4. **Keep logs** for review and learning
5. **Start small** (UNITS = 1) and increase gradually

## Getting Help

1. Check `BEGINNERS_GUIDE.md`
2. Review logs: `tail -n 100 live_trader.log`
3. Test connection: `python3 -c "import oandapyV20; print('OK')"`
4. Verify settings: `cat config.py`
