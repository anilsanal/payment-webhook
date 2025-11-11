#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /opt/payment-webhook

# Backup current version (just in case)
BACKUP_DIR="/opt/payment-webhook-backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "📦 Creating backup: backup_$TIMESTAMP"
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" --exclude='venv' --exclude='.git' --exclude='*.log' . 2>/dev/null || true

# Keep only last 5 backups
ls -t $BACKUP_DIR/backup_*.tar.gz | tail -n +6 | xargs -r rm

# Fetch latest changes
echo "📥 Fetching latest code from GitHub..."
git fetch origin main

# Check if there are changes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Already up to date!"
else
    echo "🔄 New changes detected, updating..."

    # Pull latest code
    git reset --hard origin/main

    # Check if requirements changed
    if git diff --name-only HEAD@{1} HEAD | grep -q "requirements.txt"; then
        echo "📚 Requirements changed, updating dependencies..."
        /opt/payment-webhook/venv/bin/pip install -r requirements.txt --quiet
    fi

    # Restart the service
    echo "♻️  Restarting webhook-receiver service..."
    sudo systemctl restart webhook-receiver.service

    # Wait a moment for service to start
    sleep 3

    # Check service status
    if sudo systemctl is-active --quiet webhook-receiver.service; then
        echo "✅ Service restarted successfully!"

        # Get the new version hash
        NEW_VERSION=$(git rev-parse --short HEAD)
        echo "📌 Deployed version: $NEW_VERSION"
    else
        echo "❌ Service failed to start! Rolling back..."

        # Rollback to previous version
        git reset --hard HEAD@{1}
        sudo systemctl restart webhook-receiver.service

        echo "🔙 Rolled back to previous version"
        exit 1
    fi
fi

echo "🎉 Deployment completed successfully!"
