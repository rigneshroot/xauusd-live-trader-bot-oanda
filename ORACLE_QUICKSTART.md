# Oracle Cloud Quick Start

## 🚀 3-Step Deployment

### Step 1: Upload Setup Script
```bash
# From your local machine
scp -i ~/.ssh/oracle_key setup_oracle.sh ubuntu@YOUR_ORACLE_IP:~/
```

### Step 2: Run Setup on Oracle Cloud
```bash
# SSH into Oracle
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_ORACLE_IP

# Run setup
chmod +x setup_oracle.sh
./setup_oracle.sh
```

### Step 3: Deploy Your Code
```bash
# Upload code from local machine (run this on your Mac)
./upload_to_oracle.sh YOUR_ORACLE_IP ~/.ssh/oracle_key

# Then SSH into Oracle Cloud and deploy
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_ORACLE_IP
cd ~/live-trader
./deploy.sh
```

## ✅ Done!

Your live trader is now running as a systemd service.

## 📊 Monitor

```bash
# Check status
cd ~/live-trader
./monitor.sh

# View logs
tail -f live_trader.log
```

## 🔧 Manage Service

```bash
sudo systemctl start live-trader    # Start
sudo systemctl stop live-trader     # Stop
sudo systemctl restart live-trader  # Restart
sudo systemctl status live-trader   # Status
```

## 📖 Full Documentation

See [ORACLE_DEPLOYMENT.md](file:///Users/subramanyaacharpadamanur/Documents/ScalpingStrategyOANDA/ORACLE_DEPLOYMENT.md) for complete guide.

## 💰 Oracle Cloud Free Tier

This runs **FREE forever** on Oracle Cloud's Always Free tier:
- 2 VMs with 1GB RAM each
- 200 GB storage
- 10 TB monthly bandwidth

Perfect for 24/7 live trading!
