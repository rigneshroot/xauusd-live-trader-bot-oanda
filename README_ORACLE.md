# Deployment Guide — Oracle Cloud Free Tier

This document explains how to deploy and run the **XAU/USD ORB Live Trading System** on **Oracle Cloud Free Tier** for 24/7 execution.

Oracle Free Tier provides a reliable, always-on virtual machine suitable for live trading bots.

---

## Why Oracle Cloud Free Tier

- Free forever (no credits required)
- Stable uptime
- SSH access
- Suitable for Python trading systems
- No session timeouts (unlike Colab)

This is the **recommended hosting environment** for this project.

---

## 1. Create the Oracle VM

1. Sign up at https://www.oracle.com/cloud/free/
2. Open **Oracle Cloud Console**
3. Go to:  
   **Compute → Instances → Create Instance**

### Recommended Settings
- **Image**: Ubuntu 22.04
- **Shape**: `VM.Standard.E2.1.Micro`
- **CPU / RAM**: Default (Free Tier)
- **Networking**: Default VCN with internet connectivity
- **SSH Keys**:
  - Generate a new key pair
  - Download the private key (`.key` file)

Click **Create** and wait for the instance to start.

---

## 2. Connect via SSH

On your local machine:

```bash
chmod 400 your_private_key.key
ssh -i your_private_key.key ubuntu@YOUR_PUBLIC_IP
```

You are now connected to the Oracle VM.

---

## 3. Server Setup

Update the system and install dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip git
```

Install Python packages:

```bash
pip install oandapyV20 pytz
```

---

## 4. Upload the Trading Bot

### Option A — SCP (simplest)
From your local machine:

```bash
scp *.py ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/live_bot/
```

### Option B — GitHub (recommended)
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git live_bot
cd live_bot
```

---

## 5. Configure Credentials

Edit `config.py`:

```python
OANDA_ACCOUNT_ID = "YOUR_ACCOUNT_ID"
OANDA_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
```

⚠️ **Important**  
For production safety:
- Use an OANDA token with trading-only permissions
- Avoid committing credentials to GitHub
- Consider moving credentials to environment variables later

---

## 6. First Run (Dry Run)

Always test in dry-run mode first.

In `main.py`:

```python
executor = OandaExecutor(dry_run=True)
```

Run:

```bash
python3 main.py
```

Watch logs:

```bash
tail -f live_trader.log
```

Confirm:
- OR locks at **09:35 NY**
- No trades before OR lock
- Only **one trade per session**
- Entry prices, SL, TP look correct

---

## 7. Enable Live Trading

Once validated, switch to live execution:

```python
executor = OandaExecutor(dry_run=False)
```

Restart:

```bash
python3 main.py
```

⚠️ From this point onward, **real orders are sent to OANDA**.

---

## 8. Keep the Bot Running 24/7 (systemd)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/xau_orb.service
```

Paste:

```ini
[Unit]
Description=XAU/USD ORB Live Trader
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/live_bot
ExecStart=/usr/bin/python3 /home/ubuntu/live_bot/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable xau_orb.service
sudo systemctl start xau_orb.service
```

Check status:

```bash
sudo systemctl status xau_orb.service
```

View logs:

```bash
journalctl -u xau_orb.service -f
```

---

## 9. Stopping the Bot

```bash
sudo systemctl stop xau_orb.service
```

Emergency manual stop (inside code):
```python
executor.force_close_position()
```

---

## 10. Recommended Safety Checklist

Before leaving unattended:

- [ ] Confirm dry-run behavior for at least 1 full session
- [ ] Verify one-trade-per-day enforcement
- [ ] Verify SL/TP placement accuracy
- [ ] Verify logs are updating continuously
- [ ] Verify system restarts automatically on reboot

---

## Notes on Reliability

- Oracle VMs may reboot during maintenance (rare)
- systemd ensures automatic restart
- Strategy state resets safely on restart
- SL/TP live on broker protects positions

---

## Final Notes

This deployment setup is:
- **Production-safe**
- **Cost-free**
- **Hands-off once running**

It is suitable for continuous live trading provided proper risk controls are in place.
