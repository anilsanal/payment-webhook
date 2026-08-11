#!/bin/bash
# Quick setup script for Telegram Bot

set -e

echo "=================================================="
echo "  Payment Alert Bot - Quick Setup"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f /opt/payment-webhook/.env ]; then
    echo "❌ Error: .env file not found at /opt/payment-webhook/.env"
    echo "Please create it first with database credentials."
    exit 1
fi

# Check if TELEGRAM_BOT_TOKEN is set
if ! grep -q "TELEGRAM_BOT_TOKEN=" /opt/payment-webhook/.env; then
    echo "⚠️  TELEGRAM_BOT_TOKEN not found in .env file"
    echo ""
    echo "Please follow these steps:"
    echo "1. Open Telegram and search for @BotFather"
    echo "2. Send /newbot and follow the prompts"
    echo "3. Copy the bot token"
    echo ""
    read -p "Paste your bot token here: " BOT_TOKEN
    echo "" >> /opt/payment-webhook/.env
    echo "# Telegram Bot Configuration" >> /opt/payment-webhook/.env
    echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> /opt/payment-webhook/.env
    echo "✅ Bot token added to .env"
else
    echo "✅ Bot token found in .env"
fi

echo ""

# Ask for Telegram username
echo "Enter your Telegram username (without @):"
read -p "Username: " TELEGRAM_USERNAME

if [ -z "$TELEGRAM_USERNAME" ]; then
    echo "❌ Username cannot be empty"
    exit 1
fi

echo ""
echo "Select your role:"
echo "1. admin    - Full access (recommended for first user)"
echo "2. user     - Can manage overrides and view stats"
echo "3. readonly - Can only view data"
echo ""
read -p "Enter choice (1-3) [default: 1]: " ROLE_CHOICE

case "$ROLE_CHOICE" in
    2) ROLE="user" ;;
    3) ROLE="readonly" ;;
    *) ROLE="admin" ;;
esac

echo ""
echo "Adding user: $TELEGRAM_USERNAME (role: $ROLE)"

# Add user to database
sudo -u postgres psql -d payment_transactions <<EOF > /dev/null
INSERT INTO telegram_authorized_users (telegram_username, role, added_by, added_at)
VALUES ('$TELEGRAM_USERNAME', '$ROLE', 'system', NOW())
ON CONFLICT (telegram_username)
DO UPDATE SET
    role = EXCLUDED.role,
    is_active = true;
EOF

if [ $? -eq 0 ]; then
    echo "✅ User added successfully!"
else
    echo "❌ Failed to add user to database"
    exit 1
fi

echo ""
echo "Installing and starting the bot service..."

# Copy service file
cp /tmp/payment-alert-bot.service /etc/systemd/system/ 2>/dev/null || echo "Service file already installed"

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable payment-alert-bot
systemctl start payment-alert-bot

# Wait a moment for service to start
sleep 2

# Check status
if systemctl is-active --quiet payment-alert-bot; then
    echo "✅ Bot service is running!"
else
    echo "⚠️  Bot service failed to start. Checking logs..."
    journalctl -u payment-alert-bot -n 10 --no-pager
    exit 1
fi

echo ""
echo "=================================================="
echo "  ✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Open Telegram on your phone or computer"
echo "2. Search for your bot (check @BotFather for the username)"
echo "3. Click 'Start' or send: /start"
echo "4. You should see a welcome message!"
echo ""
echo "Useful commands:"
echo "  View logs:    sudo journalctl -u payment-alert-bot -f"
echo "  Restart bot:  sudo systemctl restart payment-alert-bot"
echo "  Stop bot:     sudo systemctl stop payment-alert-bot"
echo "  Bot status:   sudo systemctl status payment-alert-bot"
echo ""
echo "  Add more users: /opt/payment-webhook/add_telegram_user.sh <username> <role>"
echo ""
echo "Full documentation: /opt/payment-webhook/TELEGRAM_BOT_GUIDE.md"
echo ""
echo "=================================================="
