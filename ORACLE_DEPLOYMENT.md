# Oracle Cloud Deployment Guide

## Quick Start

### 1. Upload Setup Script to Oracle Cloud

```bash
# From your local machine
scp -i ~/.ssh/oracle_key setup_oracle.sh ubuntu@<ORACLE_IP>:~/
```

### 2. Run Setup Script on Oracle Cloud

```bash
# SSH into Oracle Cloud
ssh -i ~/.ssh/oracle_key ubuntu@<ORACLE_IP>

# Run setup
chmod +x setup_oracle.sh
./setup_oracle.sh
```

### 3. Upload Your Trading Code

**Option A: From local machine**
```bash
# Use the generated upload script
./upload_code.sh <ORACLE_IP> ~/.ssh/oracle_key
```

**Option B: Manual upload**
```bash
scp -i ~/.ssh/oracle_key *.py ubuntu@<ORACLE_IP>:~/live-trader-src/
```

### 4. Deploy

```bash
# On Oracle Cloud
cd ~/live-trader
./deploy.sh
```

### 5. Monitor

```bash
# Check status
./monitor.sh

# View live logs
tail -f live_trader.log
```

---

## What Gets Installed

- ✅ Python 3 + pip
- ✅ Virtual environment
- ✅ Required packages (oandapyV20, pandas, pytz)
- ✅ Systemd service (auto-restart on failure)
- ✅ Log rotation (keeps last 7 days)
- ✅ Deployment script
- ✅ Monitoring script

---

## Service Commands

```bash
# Start
sudo systemctl start live-trader

# Stop
sudo systemctl stop live-trader

# Restart
sudo systemctl restart live-trader

# Status
sudo systemctl status live-trader

# Enable auto-start on boot
sudo systemctl enable live-trader

# View service logs
journalctl -u live-trader -f
```

---

## File Locations

| File | Location |
|------|----------|
| Project directory | `~/live-trader/` |
| Python files | `~/live-trader/*.py` |
| Virtual environment | `~/live-trader/venv/` |
| Logs | `~/live-trader/live_trader.log` |
| Error logs | `~/live-trader/live_trader_error.log` |
| Service file | `/etc/systemd/system/live-trader.service` |
| Upload helper | `~/upload_code.sh` |

---

## Oracle Cloud Specific Setup

### Open Firewall Ports (if needed)

```bash
# SSH access (usually already open)
sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT

# Save rules
sudo netfilter-persistent save
```

### Configure Security List (Oracle Cloud Console)

1. Go to **Networking** → **Virtual Cloud Networks**
2. Select your VCN
3. Click **Security Lists**
4. Add ingress rule for SSH (port 22) if not present

---

## Updating Code

```bash
# 1. Upload new code from local machine
./upload_code.sh <ORACLE_IP> ~/.ssh/oracle_key

# 2. Deploy on Oracle Cloud
ssh -i ~/.ssh/oracle_key ubuntu@<ORACLE_IP>
cd ~/live-trader
./deploy.sh
```

---

## Monitoring & Logs

### Real-time Monitoring

```bash
# Run monitoring dashboard
./monitor.sh

# Watch logs live
tail -f live_trader.log

# Watch errors
tail -f live_trader_error.log

# Last 100 lines
tail -n 100 live_trader.log

# Search logs
grep "ENTRY SIGNAL" live_trader.log
grep "ERROR" live_trader_error.log
```

### Download Logs to Local Machine

```bash
# From local machine
scp -i ~/.ssh/oracle_key ubuntu@<ORACLE_IP>:~/live-trader/live_trader.log .
```

---

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status live-trader

# View detailed logs
journalctl -u live-trader -n 100

# Check error log
cat ~/live-trader/live_trader_error.log

# Check Python errors
cd ~/live-trader
source venv/bin/activate
python3 live_trader.py  # Run manually to see errors
```

### Import errors

```bash
# Reinstall dependencies
cd ~/live-trader
source venv/bin/activate
pip install --upgrade oandapyV20 pandas pytz
sudo systemctl restart live-trader
```

### Out of memory

```bash
# Check memory usage
free -h

# Check process memory
ps aux | grep live_trader

# Oracle Cloud free tier has 1GB RAM
# Consider upgrading if needed
```

### Time zone issues

```bash
# Set timezone to New York
sudo timedatectl set-timezone America/New_York

# Verify
timedatectl
```

---

## Best Practices

### 1. Test with Dry-Run First

Edit `live_trader.py` to add `--dry-run` flag:
```bash
nano ~/live-trader/live_trader.py
# Or modify service file to add --dry-run
```

### 2. Monitor Daily

```bash
# Add to crontab for daily email reports
crontab -e

# Add this line (requires mail setup):
0 17 * * * tail -n 50 ~/live-trader/live_trader.log | mail -s "Live Trader Daily Report" your@email.com
```

### 3. Backup Logs Weekly

```bash
# Create backup script
cat > ~/backup_logs.sh <<'EOF'
#!/bin/bash
cd ~/live-trader
tar -czf logs_backup_$(date +%Y%m%d).tar.gz *.log
# Keep only last 4 backups
ls -t logs_backup_*.tar.gz | tail -n +5 | xargs rm -f
EOF

chmod +x ~/backup_logs.sh

# Add to crontab
crontab -e
# Add: 0 0 * * 0 ~/backup_logs.sh
```

### 4. Keep System Updated

```bash
# Weekly updates
sudo apt-get update && sudo apt-get upgrade -y
```

---

## Uninstall

```bash
# Stop service
sudo systemctl stop live-trader
sudo systemctl disable live-trader

# Remove service file
sudo rm /etc/systemd/system/live-trader.service
sudo systemctl daemon-reload

# Remove project
rm -rf ~/live-trader ~/live-trader-src

# Remove log rotation
sudo rm /etc/logrotate.d/live-trader
```

---

## Cost Optimization (Oracle Cloud Free Tier)

Oracle Cloud offers **Always Free** tier with:
- 2 AMD-based Compute VMs (1/8 OCPU, 1 GB RAM each)
- 200 GB Block Volume
- 10 TB outbound data transfer per month

**This is sufficient for running the live trader 24/7 for FREE!**

### Tips:
- Use the free tier VM (VM.Standard.E2.1.Micro)
- Enable auto-start on boot
- Monitor resource usage to stay within limits

---

## Support

If you encounter issues:

1. Check logs: `tail -f ~/live-trader/live_trader.log`
2. Check service: `sudo systemctl status live-trader`
3. Run manually: `cd ~/live-trader && source venv/bin/activate && python3 live_trader.py`
4. Check Oracle Cloud console for instance health
