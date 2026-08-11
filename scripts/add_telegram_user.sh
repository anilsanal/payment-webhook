#!/bin/bash
# Add authorized Telegram user to the bot

if [ $# -lt 1 ]; then
    echo "Usage: $0 <telegram_username> [role]"
    echo ""
    echo "Examples:"
    echo "  $0 john_doe admin       # Add admin user"
    echo "  $0 jane_doe user        # Add regular user"
    echo "  $0 bob_smith readonly   # Add readonly user"
    echo ""
    echo "Roles: admin, user, readonly (default: user)"
    exit 1
fi

TELEGRAM_USERNAME=$1
ROLE=${2:-user}

# Validate role
if [[ ! "$ROLE" =~ ^(admin|user|readonly)$ ]]; then
    echo "❌ Invalid role: $ROLE"
    echo "Valid roles: admin, user, readonly"
    exit 1
fi

echo "Adding Telegram user: $TELEGRAM_USERNAME (role: $ROLE)"

# Insert into database
sudo -u postgres psql -d payment_transactions <<EOF
INSERT INTO telegram_authorized_users (telegram_username, role, added_by, added_at)
VALUES ('$TELEGRAM_USERNAME', '$ROLE', 'system', NOW())
ON CONFLICT (telegram_username)
DO UPDATE SET
    role = EXCLUDED.role,
    is_active = true;

SELECT
    telegram_username,
    role,
    is_active,
    added_at
FROM telegram_authorized_users
WHERE telegram_username = '$TELEGRAM_USERNAME';
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ User added successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start the bot: sudo systemctl start payment-alert-bot"
    echo "2. Open Telegram and search for your bot"
    echo "3. Send /start to begin using the bot"
else
    echo "❌ Failed to add user"
    exit 1
fi
