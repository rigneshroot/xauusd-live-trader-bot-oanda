# OANDA Gold Trader

Automated live trading system for gold (XAU/USD) on OANDA using the Opening Range breakout strategy. Built with Python, designed for 24/7 deployment on Oracle Cloud Free Tier.

## 📈 What It Does

This bot automatically trades gold (XAU/USD) by:
- Monitoring the Opening Range (9:30-9:34 AM NY time)
- Detecting breakout and retest patterns
- Executing trades with automatic stop loss and take profit
- Managing one trade per day maximum
- Running 24/7 on cloud infrastructure

## 🚀 Features

- **Gold Trading (XAU/USD)**: Optimized for gold, adaptable to other forex pairs
- **Real-time Trading**: Connects to OANDA streaming API for live price data
- **Opening Range Strategy**: Trades breakouts from the 9:30-9:34 AM NY range
- **Two Entry Models**: Retest + Displacement and Fair Value Gap patterns
- **Risk Management**: Automatic SL/TP on every trade, one trade per day maximum
- **Cloud Deployment**: Run 24/7 on Oracle Cloud Free Tier (forever free)
- **Beginner-Friendly**: Comprehensive guides and interactive setup scripts
- **Backtesting**: Includes original backtesting script for strategy validation

## 📋 Prerequisites

- Python 3.8+
- OANDA practice/live account
- OANDA API credentials ([Get them here](https://www.oanda.com/))

## ⚡ Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd xauusd-live-trader-oanda
```

### 2. Install Dependencies

```bash
pip3 install oandapyV20 pandas pytz
```

### 3. Configure

```bash
# Copy template and edit with your credentials
cp config.template.py config.py
nano config.py  # Add your OANDA_ACCOUNT_ID and OANDA_ACCESS_TOKEN
```

### 4. Run (Practice Mode)

```bash
# Interactive menu
./start_trading.sh

# Or manually
python3 live_trader.py --dry-run
```

## 📚 Documentation

- **[BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md)** - Complete beginner's guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Daily commands and cheat sheet
- **[ORACLE_QUICKSTART.md](ORACLE_QUICKSTART.md)** - Deploy to Oracle Cloud
- **[SERVICE_COMMANDS.md](SERVICE_COMMANDS.md)** - Service management reference

## 🏗️ Architecture

### Core Files

| File | Purpose |
|------|---------|
| `live_trader.py` | Main orchestrator |
| `candle_buffer.py` | Rolling candle buffer |
| `session_state.py` | Session state machine |
| `entry_detector.py` | Entry signal detection |
| `oanda_executor.py` | Order execution |
| `streaming_client.py` | OANDA streaming API |
| `utils.py` | Helper functions |
| `config.py` | Configuration (not in Git) |

### Alternative Versions

- **`live_trader_colab.py`** - Single-file Google Colab version
- **`scalping_strategy_works.py`** - Original backtesting script

## 🔧 Configuration

Edit `config.py` to adjust:

```python
INSTRUMENT = 'XAU_USD'     # Gold (default) - can change to EUR_USD, GBP_USD, etc.
UNITS = 3                  # Position size (start with 1)
RISK_REWARD = 2            # TP = 2x SL distance
SKIP_FIRST_N = 5           # Wait time after OR lock
RETEST_PCT = 0.05          # Retest tolerance (5%)
```

### Supported Instruments

While optimized for gold (XAU/USD), the system works with any OANDA instrument:
- **Metals**: XAU_USD (Gold), XAG_USD (Silver)
- **Major Forex**: EUR_USD, GBP_USD, USD_JPY
- **Commodities**: Check OANDA for available instruments

See [config.template.py](config.template.py) for all options.

## 🌐 Deployment

### Local (Mac/Linux)

```bash
python3 live_trader.py --dry-run  # Practice
python3 live_trader.py            # Live
```

### Oracle Cloud (24/7 Free)

```bash
# Upload setup script
scp -i ~/.ssh/oracle_key setup_oracle.sh ubuntu@YOUR_IP:~/

# Run setup
ssh -i ~/.ssh/oracle_key ubuntu@YOUR_IP
./setup_oracle.sh

# Deploy code
./upload_to_oracle.sh YOUR_IP ~/.ssh/oracle_key
```

See [ORACLE_QUICKSTART.md](ORACLE_QUICKSTART.md) for details.

### Google Colab

Upload `live_trader_colab.py` to Colab and run:
```python
!pip install oandapyV20 pandas pytz
main(dry_run=True)  # Practice mode
```

## 🛡️ Safety Features

- ✅ **Dry-run mode** - Test without real orders
- ✅ **One trade per day** - Enforced by state machine
- ✅ **Mandatory SL/TP** - Every order has stops
- ✅ **Practice account** - Test on paper trading first
- ✅ **Emergency close** - Manual intervention available

## 📊 How It Works

1. **9:30 AM NY** - Market opens, start collecting OR candles
2. **9:35 AM NY** - Lock Opening Range (high/low)
3. **After 9:35** - Monitor for breakout + retest
4. **Signal Detected** - Place order with SL/TP
5. **One Trade Max** - Session closes after trade

## 🧪 Testing

```bash
# Dry-run (no real orders)
python3 live_trader.py --dry-run

# Paper trading (practice account)
python3 live_trader.py  # Make sure config.py uses practice account

# Backtest (historical data)
python3 scalping_strategy_works.py
```

## 📝 Logs

```bash
# View logs
tail -f live_trader.log

# Search for signals
grep "ENTRY SIGNAL" live_trader.log

# Search for errors
grep "ERROR" live_trader.log
```

## 🆘 Troubleshooting

### Module not found
```bash
pip3 install oandapyV20 pandas pytz
```

### Permission denied
```bash
chmod +x start_trading.sh
chmod +x upload_to_oracle.sh
```

### Connection refused
- Check OANDA credentials in `config.py`
- Verify internet connection
- Check OANDA API status

See [BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md) for more help.

## ⚠️ Important Notes

1. **Start with practice account** - Never test on live money
2. **Use dry-run mode first** - Test for at least a week
3. **One trade per day** - System enforces this automatically
4. **Monitor regularly** - Check logs during market hours
5. **Keep credentials secure** - Never commit `config.py` to Git

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## ⚡ Performance

- **Memory**: ~50MB (optimized candle buffer)
- **CPU**: Minimal (event-driven)
- **Network**: ~1KB/sec (streaming)
- **Latency**: <100ms (tick to processing)

## 🔐 Security

- API credentials stored in `config.py` (not tracked by Git)
- Use environment variables for production
- Practice account recommended for testing
- All orders include SL/TP for risk management

## 📞 Support

- Check [BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md) first
- Review logs: `tail -f live_trader.log`
- Test connection: `python3 -c "import oandapyV20; print('OK')"`
- Open an issue for bugs

## 🎯 Roadmap

- [ ] Multi-instrument support
- [ ] Web dashboard for monitoring
- [ ] Telegram notifications
- [ ] Advanced position sizing
- [ ] Machine learning signal filtering

---

## 👤 Author

**Rignesh**

---

**Made with ❤️ for algorithmic traders**

**Disclaimer**: Trading involves risk. This software is for educational purposes. Always test on a practice account first.
