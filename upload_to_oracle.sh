#!/bin/bash
###############################################################################
# Upload Live Trader Code to Oracle Cloud
# Run this script from your LOCAL machine (Mac)
#
# Usage:
#   ./upload_code.sh <ORACLE_IP> [SSH_KEY_PATH]
#
# Example:
#   ./upload_code.sh 123.45.67.89 ~/.ssh/oracle_key
###############################################################################

set -e

# Get arguments
ORACLE_IP="${1:-}"
SSH_KEY="${2:-~/.ssh/id_rsa}"

# Check if IP provided
if [ -z "$ORACLE_IP" ]; then
    echo "❌ Error: Oracle Cloud IP address required"
    echo ""
    echo "Usage: ./upload_code.sh <ORACLE_IP> [SSH_KEY_PATH]"
    echo ""
    echo "Example:"
    echo "  ./upload_code.sh 123.45.67.89 ~/.ssh/oracle_key"
    echo ""
    exit 1
fi

# Expand tilde in SSH key path
SSH_KEY="${SSH_KEY/#\~/$HOME}"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    echo ""
    echo "Common locations:"
    echo "  ~/.ssh/id_rsa"
    echo "  ~/.ssh/oracle_key"
    echo "  ~/.ssh/id_ed25519"
    echo ""
    exit 1
fi

echo "=========================================="
echo "📤 Uploading Live Trader to Oracle Cloud"
echo "=========================================="
echo ""
echo "Target IP: $ORACLE_IP"
echo "SSH Key:   $SSH_KEY"
echo ""

# Test SSH connection
echo "🔑 Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o BatchMode=yes ubuntu@$ORACLE_IP "echo 'Connection successful'" 2>/dev/null; then
    echo "❌ Error: Cannot connect to Oracle Cloud"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if IP is correct: $ORACLE_IP"
    echo "2. Check if SSH key is correct: $SSH_KEY"
    echo "3. Check if port 22 is open in Oracle Cloud Security List"
    echo "4. Try manual connection: ssh -i $SSH_KEY ubuntu@$ORACLE_IP"
    echo ""
    exit 1
fi

echo "✅ SSH connection successful"
echo ""

# Create remote directory
echo "📁 Creating remote directory..."
ssh -i "$SSH_KEY" ubuntu@$ORACLE_IP "mkdir -p ~/live-trader-src"

# Upload Python files
echo "📦 Uploading Python files..."
scp -i "$SSH_KEY" \
    config.py \
    utils.py \
    candle_buffer.py \
    session_state.py \
    entry_detector.py \
    oanda_executor.py \
    streaming_client.py \
    live_trader.py \
    emergency_close.py \
    ubuntu@$ORACLE_IP:~/live-trader-src/

echo ""
echo "=========================================="
echo "✅ Upload Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. SSH into Oracle Cloud:"
echo "   ssh -i $SSH_KEY ubuntu@$ORACLE_IP"
echo ""
echo "2. Run setup (first time only):"
echo "   chmod +x setup_oracle.sh"
echo "   ./setup_oracle.sh"
echo ""
echo "3. Deploy the code:"
echo "   cd ~/live-trader"
echo "   ./deploy.sh"
echo ""
echo "4. Monitor the service:"
echo "   ./monitor.sh"
echo ""
