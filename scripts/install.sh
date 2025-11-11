#!/bin/bash

# Installation Script for Payment Gateway Webhook Receiver
# Run this script as root or with sudo

set -e  # Exit on error

echo "=========================================="
echo "Payment Webhook Receiver - Installation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/payment-webhook"
VENV_DIR="$PROJECT_DIR/venv"
APP_FILE="$PROJECT_DIR/webhook_app.py"
SCHEMA_FILE="$PROJECT_DIR/database_schema.sql"
SERVICE_FILE="/etc/systemd/system/webhook-receiver.service"
LOG_DIR="/var/log"

echo -e "${YELLOW}Step 1: Installing Python dependencies...${NC}"
cd $PROJECT_DIR
source $VENV_DIR/bin/activate

pip install --upgrade pip
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install psycopg2-binary==2.9.9
pip install python-multipart==0.0.6

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating database schema...${NC}"
echo "This will create the tables: webhook_events, transactions, bin_bank_mapping"

# Run the schema SQL
sudo -u postgres psql -d payment_transactions -f $SCHEMA_FILE

echo -e "${GREEN}✓ Database schema created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating systemd service...${NC}"

# Create systemd service file
cat > $SERVICE_FILE << 'EOF'
[Unit]
Description=Payment Gateway Webhook Receiver
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/payment-webhook
Environment="PATH=/opt/payment-webhook/venv/bin"
ExecStart=/opt/payment-webhook/venv/bin/python -m uvicorn webhook_app:app --host 0.0.0.0 --port 8000 --log-level info
Restart=always
RestartSec=10

# Environment variables
Environment="DB_NAME=payment_transactions"
Environment="DB_USER=webhook_user"
Environment="DB_PASSWORD=yingyanganil5s"
Environment="DB_HOST=localhost"
Environment="DB_PORT=5432"

# Security settings
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=append:/var/log/webhook_receiver.log
StandardError=append:/var/log/webhook_receiver_error.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service file created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Creating log files...${NC}"
touch /var/log/webhook_receiver.log
touch /var/log/webhook_receiver_error.log
chmod 644 /var/log/webhook_receiver.log
chmod 644 /var/log/webhook_receiver_error.log

echo -e "${GREEN}✓ Log files created${NC}"
echo ""

echo -e "${YELLOW}Step 5: Enabling and starting the service...${NC}"

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable webhook-receiver.service

# Start the service
systemctl start webhook-receiver.service

# Wait a moment for service to start
sleep 3

# Check status
if systemctl is-active --quiet webhook-receiver.service; then
    echo -e "${GREEN}✓ Service is running!${NC}"
else
    echo -e "${RED}✗ Service failed to start. Check logs with: journalctl -u webhook-receiver.service -f${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Service Status:"
systemctl status webhook-receiver.service --no-pager -l
echo ""
echo "Useful Commands:"
echo "  - Check status:      systemctl status webhook-receiver"
echo "  - View logs:         tail -f /var/log/webhook_receiver.log"
echo "  - View error logs:   tail -f /var/log/webhook_receiver_error.log"
echo "  - Restart service:   systemctl restart webhook-receiver"
echo "  - Stop service:      systemctl stop webhook-receiver"
echo "  - View real-time:    journalctl -u webhook-receiver -f"
echo ""
echo "Test the webhook receiver:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Next steps:"
echo "  1. Configure Nginx as reverse proxy (for HTTPS)"
echo "  2. Point your domain to this server"
echo "  3. Install Metabase"
echo "  4. Populate bin_bank_mapping table with your BIN list"
echo ""
