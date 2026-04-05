#!/bin/bash
# Ghost Alpha VWAP Reclaim — Deploy to newvultr
# Usage: bash algo/deploy.sh

set -e

SERVER="newvultr"
REMOTE_DIR="/home/mphinance/algo"
LOCAL_DIR="$(dirname "$0")"

echo "👻 Deploying Ghost VWAP Algo to ${SERVER}..."

# 1. Create remote directory
echo "📁 Creating remote directory..."
ssh $SERVER "mkdir -p ${REMOTE_DIR}/data"

# 2. Rsync algo files
echo "📦 Syncing algo files..."
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
    ${LOCAL_DIR}/ghost_vwap_algo.py \
    ${LOCAL_DIR}/config.py \
    ${LOCAL_DIR}/requirements.txt \
    ${LOCAL_DIR}/ghost-vwap-algo.service \
    ${SERVER}:${REMOTE_DIR}/

# 3. Copy secrets.env (from mphinance root)
echo "🔐 Copying secrets..."
SECRETS_FILE="$(dirname "$LOCAL_DIR")/secrets.env"
if [ -f "$SECRETS_FILE" ]; then
    rsync -avz "$SECRETS_FILE" ${SERVER}:${REMOTE_DIR}/secrets.env
    ssh $SERVER "chmod 600 ${REMOTE_DIR}/secrets.env"
else
    echo "⚠️  No secrets.env found at $SECRETS_FILE"
    echo "   You'll need to manually copy it to ${REMOTE_DIR}/secrets.env"
fi

# 4. Install Python deps
echo "📦 Installing dependencies..."
ssh $SERVER "pip3 install -r ${REMOTE_DIR}/requirements.txt 2>/dev/null || true"

# 5. Install systemd service
echo "⚙️  Installing systemd service..."
ssh $SERVER "sudo cp ${REMOTE_DIR}/ghost-vwap-algo.service /etc/systemd/system/"
ssh $SERVER "sudo systemctl daemon-reload"
ssh $SERVER "sudo systemctl enable ghost-vwap-algo.service"
ssh $SERVER "sudo systemctl restart ghost-vwap-algo.service"

# 6. Check status
echo ""
echo "📊 Service status:"
ssh $SERVER "sudo systemctl status ghost-vwap-algo.service --no-pager" || true
echo ""
echo "📋 Recent logs:"
ssh $SERVER "sudo journalctl -u ghost-vwap-algo -n 20 --no-pager" || true

echo ""
echo "✅ Deployment complete!"
echo "   Monitor: ssh $SERVER 'sudo journalctl -u ghost-vwap-algo -f'"
echo "   Stop:    ssh $SERVER 'sudo systemctl stop ghost-vwap-algo'"
echo "   Start:   ssh $SERVER 'sudo systemctl start ghost-vwap-algo'"
