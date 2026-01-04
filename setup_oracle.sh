#!/bin/bash
###############################################################################
# Live Trading System - Oracle Cloud Setup Script
# 
# This script sets up the live trading system on Oracle Cloud Infrastructure
# (or any Ubuntu/Debian-based Linux server)
#
# Usage:
#   chmod +x setup_oracle.sh
#   ./setup_oracle.sh
###############################################################################

set -e  # Exit on error

echo "=========================================="
echo "Live Trading System - Oracle Cloud Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please do not run as root. Run as regular user with sudo access."
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3 and pip
echo "🐍 Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt-get install -y git curl wget tmux htop

# Create project directory
PROJECT_DIR="$HOME/live-trader"
echo "📁 Creating project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create Python virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install oandapyV20 pandas pytz

# Create systemd service file
echo "⚙️  Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/live-trader.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Live Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/live_trader.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$PROJECT_DIR/live_trader.log
StandardError=append:$PROJECT_DIR/live_trader_error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service created at $SERVICE_FILE"

# Create log rotation config
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/live-trader > /dev/null <<EOF
$PROJECT_DIR/live_trader.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
}
EOF

# Create deployment script
echo "📜 Creating deployment script..."
cat > "$PROJECT_DIR/deploy.sh" <<'EOF'
#!/bin/bash
# Deploy/update live trader code

set -e

echo "🚀 Deploying live trader..."

# Stop service if running
sudo systemctl stop live-trader || true

# Pull latest code (if using git)
# git pull origin main

# Copy files from local directory
# Assumes you've uploaded files to ~/live-trader-src/
if [ -d "$HOME/live-trader-src" ]; then
    echo "📋 Copying files..."
    cp -r $HOME/live-trader-src/*.py .
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install --upgrade oandapyV20 pandas pytz

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start live-trader

# Enable service to start on boot
sudo systemctl enable live-trader

echo "✅ Deployment complete!"
echo "📊 Check status: sudo systemctl status live-trader"
echo "📝 View logs: tail -f live_trader.log"
EOF

chmod +x "$PROJECT_DIR/deploy.sh"

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > "$PROJECT_DIR/monitor.sh" <<'EOF'
#!/bin/bash
# Monitor live trader

echo "=========================================="
echo "Live Trader Monitoring"
echo "=========================================="
echo ""

# Service status
echo "📊 Service Status:"
sudo systemctl status live-trader --no-pager | head -n 10
echo ""

# Recent logs
echo "📝 Recent Logs (last 20 lines):"
tail -n 20 live_trader.log
echo ""

# Check if process is running
if pgrep -f "live_trader.py" > /dev/null; then
    echo "✅ Live trader is running"
    
    # Show resource usage
    echo ""
    echo "💻 Resource Usage:"
    ps aux | grep live_trader.py | grep -v grep
else
    echo "❌ Live trader is NOT running"
fi
EOF

chmod +x "$PROJECT_DIR/monitor.sh"

# Create quick start guide
echo "📖 Creating quick start guide..."
cat > "$PROJECT_DIR/ORACLE_SETUP.md" <<'EOF'
# Oracle Cloud Setup Guide

## Files Uploaded

Your live trader is installed at: `~/live-trader/`

## Upload Your Code

1. **Upload files to Oracle Cloud**:
   ```bash
   # From your local machine
   scp -i ~/.ssh/oracle_key *.py ubuntu@<ORACLE_IP>:~/live-trader-src/
   ```

2. **Deploy**:
   ```bash
   cd ~/live-trader
   ./deploy.sh
   ```

## Service Management

```bash
# Start service
sudo systemctl start live-trader

# Stop service
sudo systemctl stop live-trader

# Restart service
sudo systemctl restart live-trader

# Check status
sudo systemctl status live-trader

# Enable auto-start on boot
sudo systemctl enable live-trader

# Disable auto-start
sudo systemctl disable live-trader
```

## Monitoring

```bash
# Run monitoring script
cd ~/live-trader
./monitor.sh

# View live logs
tail -f live_trader.log

# View error logs
tail -f live_trader_error.log

# View last 100 lines
tail -n 100 live_trader.log
```

## Configuration

Edit your configuration:
```bash
cd ~/live-trader
nano config.py
```

After editing, restart the service:
```bash
sudo systemctl restart live-trader
```

## Troubleshooting

### Service won't start
```bash
# Check logs
journalctl -u live-trader -n 50

# Check error log
cat live_trader_error.log
```

### Update Python packages
```bash
cd ~/live-trader
source venv/bin/activate
pip install --upgrade oandapyV20 pandas pytz
sudo systemctl restart live-trader
```

### Check if port is blocked
```bash
# Oracle Cloud requires opening ports in firewall
sudo iptables -L
```

## Firewall Configuration (Oracle Cloud)

If you need to access the server remotely:

```bash
# Allow SSH (if not already)
sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT

# Save rules
sudo netfilter-persistent save
```

## Backup Logs

```bash
# Create backup
tar -czf logs_backup_$(date +%Y%m%d).tar.gz *.log

# Download to local machine
scp -i ~/.ssh/oracle_key ubuntu@<ORACLE_IP>:~/live-trader/logs_backup_*.tar.gz .
```

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop live-trader
sudo systemctl disable live-trader

# Remove service file
sudo rm /etc/systemd/system/live-trader.service
sudo systemctl daemon-reload

# Remove project directory
rm -rf ~/live-trader
```
EOF

# Create upload helper script
cat > "$HOME/upload_code.sh" <<EOF
#!/bin/bash
# Helper script to upload code from local machine to Oracle Cloud
# Run this on your LOCAL machine, not on Oracle Cloud

ORACLE_IP="\${1:-YOUR_ORACLE_IP}"
SSH_KEY="\${2:-~/.ssh/oracle_key}"

if [ "\$ORACLE_IP" = "YOUR_ORACLE_IP" ]; then
    echo "Usage: ./upload_code.sh <ORACLE_IP> [SSH_KEY_PATH]"
    echo "Example: ./upload_code.sh 123.45.67.89 ~/.ssh/oracle_key"
    exit 1
fi

echo "📤 Uploading code to Oracle Cloud..."
echo "IP: \$ORACLE_IP"
echo "Key: \$SSH_KEY"
echo ""

# Create remote directory
ssh -i "\$SSH_KEY" ubuntu@\$ORACLE_IP "mkdir -p ~/live-trader-src"

# Upload Python files
scp -i "\$SSH_KEY" *.py ubuntu@\$ORACLE_IP:~/live-trader-src/

echo ""
echo "✅ Upload complete!"
echo ""
echo "Next steps:"
echo "1. SSH into Oracle Cloud: ssh -i \$SSH_KEY ubuntu@\$ORACLE_IP"
echo "2. Deploy: cd ~/live-trader && ./deploy.sh"
EOF

chmod +x "$HOME/upload_code.sh"

# Print completion message
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "📝 Service file: $SERVICE_FILE"
echo ""
echo "Next Steps:"
echo "1. Upload your Python files:"
echo "   - From local machine: ./upload_code.sh <ORACLE_IP> <SSH_KEY>"
echo "   - Or manually: scp *.py ubuntu@<IP>:~/live-trader-src/"
echo ""
echo "2. Deploy the code:"
echo "   cd $PROJECT_DIR"
echo "   ./deploy.sh"
echo ""
echo "3. Monitor the service:"
echo "   ./monitor.sh"
echo ""
echo "4. View logs:"
echo "   tail -f live_trader.log"
echo ""
echo "📖 Full guide: $PROJECT_DIR/ORACLE_SETUP.md"
echo ""
