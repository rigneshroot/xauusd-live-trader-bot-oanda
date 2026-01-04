#!/bin/bash
###############################################################################
# BEGINNER-FRIENDLY RUN SCRIPT
# 
# This script makes it easy to start the live trader
# Just run: ./start_trading.sh
###############################################################################

echo "=========================================="
echo "🚀 Live Trading System"
echo "=========================================="
echo ""

# Check if in correct directory
if [ ! -f "live_trader.py" ]; then
    echo "❌ Error: Please run this script from the project directory"
    echo ""
    echo "Try:"
    echo "  cd /Users/subramanyaacharpadamanur/Documents/ScalpingStrategyOANDA"
    echo "  ./start_trading.sh"
    exit 1
fi

# Show menu
echo "Choose mode:"
echo ""
echo "1) DRY RUN (Practice - no real orders)"
echo "2) LIVE TRADING (Real orders - use with caution!)"
echo "3) View logs"
echo "4) Stop trading"
echo "5) Emergency close all positions"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🎯 Starting in DRY RUN mode..."
        echo "This will NOT place real orders"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""
        sleep 2
        python3 live_trader.py --dry-run
        ;;
    2)
        echo ""
        echo "⚠️  WARNING: LIVE TRADING MODE"
        echo "This WILL place REAL orders with REAL money!"
        echo ""
        read -p "Are you sure? Type 'YES' to continue: " confirm
        if [ "$confirm" = "YES" ]; then
            echo ""
            echo "🔴 Starting LIVE trading..."
            echo "Press Ctrl+C to stop"
            echo ""
            sleep 2
            python3 live_trader.py
        else
            echo "Cancelled."
        fi
        ;;
    3)
        echo ""
        echo "📝 Showing last 50 lines of log..."
        echo "Press Ctrl+C to exit"
        echo ""
        tail -f -n 50 live_trader.log
        ;;
    4)
        echo ""
        echo "🛑 Stopping trading..."
        pkill -f "live_trader.py"
        echo "✅ Stopped"
        ;;
    5)
        echo ""
        echo "🚨 EMERGENCY CLOSE"
        echo "This will close ALL open positions immediately!"
        echo ""
        read -p "Are you sure? Type 'YES' to continue: " confirm
        if [ "$confirm" = "YES" ]; then
            python3 emergency_close.py
        else
            echo "Cancelled."
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
