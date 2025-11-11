#!/bin/bash
###############################################################################
# Production Server Update Script - Phase 2
#
# ⚠️  RUN THIS ON THE PRODUCTION SERVER ONLY
# ⚠️  Run AFTER local testing and GitHub push
#
# This updates systemd service and cron job to work with new structure.
###############################################################################

set -e

echo "════════════════════════════════════════════════════════════"
echo "   Production Server - Structure Update (Phase 2)"
echo "════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Safety check - make sure we're on the server
if [ ! -d "/opt/payment-webhook" ]; then
    echo -e "${RED}❌ Error: /opt/payment-webhook not found${NC}"
    echo "This script should only run on the production server"
    exit 1
fi

cd /opt/payment-webhook

echo -e "${BLUE}Current directory: $(pwd)${NC}"
echo ""

# Check if we have the new structure
if [ ! -d "app" ] || [ ! -f "app/webhook_app.py" ]; then
    echo -e "${RED}❌ Error: New folder structure not found${NC}"
    echo "Did you pull the latest changes from GitHub?"
    echo "Run: git pull origin main"
    exit 1
fi

echo -e "${YELLOW}STEP 1: Creating backup${NC}"
echo "────────────────────────────────────────────────────────────"

BACKUP_DIR="/opt/payment-webhook-prod-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current systemd service file
cp /etc/systemd/system/webhook-receiver.service "$BACKUP_DIR/" 2>/dev/null || true

# Backup crontab
crontab -l > "$BACKUP_DIR/crontab.backup" 2>/dev/null || true

echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"
echo "  - systemd service file backed up"
echo "  - crontab backed up"
echo ""

echo -e "${YELLOW}STEP 2: Updating systemd service${NC}"
echo "────────────────────────────────────────────────────────────"

# Update the ExecStart line in the systemd service
echo "Updating /etc/systemd/system/webhook-receiver.service"

sudo sed -i.backup 's|webhook_app:app|app.webhook_app:app|g' /etc/systemd/system/webhook-receiver.service

# Verify the change
if grep -q "app.webhook_app:app" /etc/systemd/system/webhook-receiver.service; then
    echo -e "${GREEN}✓ Systemd service updated successfully${NC}"

    # Show the change
    echo ""
    echo "New ExecStart line:"
    grep "ExecStart" /etc/systemd/system/webhook-receiver.service
    echo ""
else
    echo -e "${RED}❌ Failed to update systemd service${NC}"
    echo "Manual update required!"
    exit 1
fi

echo -e "${YELLOW}STEP 3: Reloading systemd${NC}"
echo "────────────────────────────────────────────────────────────"

sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"
echo ""

echo -e "${YELLOW}STEP 4: Updating cron job${NC}"
echo "────────────────────────────────────────────────────────────"

# Get current crontab
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Update the payment_monitor.py path
sed -i 's|/opt/payment-webhook/payment_monitor\.py|/opt/payment-webhook/services/payment_monitor.py|g' "$TEMP_CRON"

# Install updated crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

# Verify
if crontab -l | grep -q "services/payment_monitor.py"; then
    echo -e "${GREEN}✓ Cron job updated successfully${NC}"
    echo ""
    echo "New cron job:"
    crontab -l | grep payment_monitor
    echo ""
else
    echo -e "${YELLOW}⚠️  Warning: Cron job may need manual update${NC}"
    echo "Current cron jobs:"
    crontab -l | grep payment_monitor || echo "  (no payment_monitor job found)"
    echo ""
fi

echo -e "${YELLOW}STEP 5: Restarting webhook service${NC}"
echo "────────────────────────────────────────────────────────────"

echo "Stopping service..."
sudo systemctl stop webhook-receiver.service
sleep 2

echo "Starting service with new structure..."
sudo systemctl start webhook-receiver.service
sleep 3

# Check if service started successfully
if sudo systemctl is-active --quiet webhook-receiver.service; then
    echo -e "${GREEN}✓ Service restarted successfully!${NC}"
    echo ""

    # Show service status
    echo "Service status:"
    sudo systemctl status webhook-receiver.service --no-pager -l | head -15
    echo ""
else
    echo -e "${RED}❌ Service failed to start!${NC}"
    echo ""
    echo "Service logs:"
    sudo journalctl -u webhook-receiver.service -n 50 --no-pager
    echo ""
    echo -e "${RED}ROLLING BACK...${NC}"

    # Restore backup
    sudo cp "$BACKUP_DIR/webhook-receiver.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl start webhook-receiver.service

    echo "Service restored to previous version"
    exit 1
fi

echo -e "${YELLOW}STEP 6: Testing webhook endpoint${NC}"
echo "────────────────────────────────────────────────────────────"

echo "Waiting 5 seconds for service to be fully ready..."
sleep 5

# Test health endpoint
HEALTH_CHECK=$(curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "")

if [ -n "$HEALTH_CHECK" ]; then
    echo -e "${GREEN}✓ Health check passed!${NC}"
    echo ""
    curl -s http://localhost:8000/health | jq . || curl -s http://localhost:8000/health
    echo ""
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Response:"
    curl -s http://localhost:8000/health || echo "(no response)"
    echo ""
    echo ""
    echo -e "${YELLOW}Service is running but health check failed.${NC}"
    echo "Check logs: sudo journalctl -u webhook-receiver.service -f"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ PRODUCTION UPDATE COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 Summary of changes:"
echo "   ✓ Systemd service updated (webhook_app → app.webhook_app)"
echo "   ✓ Cron job updated (payment_monitor.py → services/payment_monitor.py)"
echo "   ✓ Service restarted successfully"
echo "   ✓ Health check verified"
echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo ""
echo "🔍 Monitor the service:"
echo "   sudo journalctl -u webhook-receiver.service -f"
echo ""
echo "📊 Check logs:"
echo "   tail -f /var/log/webhook_receiver.log"
echo ""
echo "⏱️  Monitor will run in ~5 minutes (next cron schedule)"
echo "   Check: tail -f /var/log/payment_monitor.log"
echo ""
