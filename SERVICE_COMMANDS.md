# Service Management Quick Reference

## Essential Commands

### Status & Monitoring
```bash
# Check if running
sudo systemctl status live-trader

# View live logs
tail -f ~/live-trader/live_trader.log

# Quick monitor (status + logs + resources)
~/live-trader/monitor.sh
```

### Start/Stop/Restart
```bash
# Start
sudo systemctl start live-trader

# Stop
sudo systemctl stop live-trader

# Restart (after config changes)
sudo systemctl restart live-trader
```

### Auto-Start on Boot
```bash
# Enable (already enabled by default)
sudo systemctl enable live-trader

# Disable
sudo systemctl disable live-trader

# Check
systemctl is-enabled live-trader
```

---

## Log Commands

```bash
# Last 50 lines
tail -n 50 ~/live-trader/live_trader.log

# Search for signals
grep "ENTRY SIGNAL" ~/live-trader/live_trader.log

# Search for errors
grep "ERROR" ~/live-trader/live_trader.log

# Search for OR locks
grep "OR LOCKED" ~/live-trader/live_trader.log

# System journal
journalctl -u live-trader -n 50
```

---

## Common Tasks

### Daily Check
```bash
sudo systemctl status live-trader
tail -n 100 ~/live-trader/live_trader.log
```

### After Editing config.py
```bash
nano ~/live-trader/config.py
sudo systemctl restart live-trader
sudo systemctl status live-trader
```

### Emergency Stop All
```bash
sudo systemctl stop live-trader
python3 ~/live-trader/emergency_close.py
```

---

## Troubleshooting

```bash
# Detailed error logs
journalctl -u live-trader -n 100 --no-pager

# Error log file
cat ~/live-trader/live_trader_error.log

# Run manually to see errors
cd ~/live-trader
source venv/bin/activate
python3 live_trader.py --dry-run
```

---

## Bash Aliases (Optional)

Add to `~/.bashrc`:
```bash
alias ts='sudo systemctl status live-trader'
alias tstart='sudo systemctl start live-trader'
alias tstop='sudo systemctl stop live-trader'
alias tlogs='tail -f ~/live-trader/live_trader.log'
alias tmon='~/live-trader/monitor.sh'
```

Then: `source ~/.bashrc`

Use: `ts`, `tlogs`, `tmon`, etc.
