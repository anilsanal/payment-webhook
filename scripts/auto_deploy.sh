#!/bin/bash
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/anil/Projects/payment-webhook"
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
REMOTE_DIR="/opt/payment-webhook"

echo -e "${BLUE}🚀 Automated Deployment Script${NC}"
echo -e "${BLUE}================================${NC}\n"

# Function to check if we're in the right directory
check_directory() {
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        echo -e "${RED}❌ Error: Not in a git repository${NC}"
        echo "Please run this script from: $PROJECT_DIR"
        exit 1
    fi
}

# Function to check for uncommitted changes
check_git_status() {
    cd "$PROJECT_DIR"

    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
        git status --short
        echo ""
        read -p "Do you want to commit these changes? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            return 0
        else
            echo -e "${RED}❌ Aborting deployment${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ No uncommitted changes${NC}"
}

# Function to push to GitHub
push_to_github() {
    cd "$PROJECT_DIR"

    echo -e "\n${BLUE}📤 Pushing to GitHub...${NC}"

    # Try to push with credential helper
    if git push origin main 2>&1; then
        echo -e "${GREEN}✅ Successfully pushed to GitHub${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Push failed - trying alternative methods${NC}"

        # Check if we can use SSH
        echo -e "${BLUE}Attempting to switch to SSH...${NC}"
        CURRENT_REMOTE=$(git remote get-url origin)

        if [[ $CURRENT_REMOTE == https://* ]]; then
            # Convert HTTPS to SSH
            SSH_REMOTE=$(echo $CURRENT_REMOTE | sed 's|https://github.com/|git@github.com:|')

            echo -e "${BLUE}Switching remote from HTTPS to SSH${NC}"
            git remote set-url origin "$SSH_REMOTE"

            # Try SSH push
            if git push origin main 2>&1; then
                echo -e "${GREEN}✅ Successfully pushed via SSH${NC}"
                return 0
            else
                echo -e "${RED}❌ SSH push failed${NC}"
                # Revert to HTTPS
                git remote set-url origin "$CURRENT_REMOTE"

                echo -e "\n${YELLOW}Manual authentication required.${NC}"
                echo -e "Please run: ${BLUE}git push origin main${NC}"
                echo -e "Then run this script again to continue deployment."
                exit 1
            fi
        fi
    fi
}

# Function to deploy to server
deploy_to_server() {
    echo -e "\n${BLUE}🚀 Deploying to server...${NC}"

    # Check if SSH is configured
    if ! ssh -q "$SERVER_USER@$SERVER_HOST" exit 2>/dev/null; then
        echo -e "${RED}❌ Cannot connect to server: $SERVER_USER@$SERVER_HOST${NC}"
        echo -e "${YELLOW}Please configure SSH access or set SERVER_USER and SERVER_HOST${NC}"
        echo -e "Example: ${BLUE}export SERVER_HOST=192.168.1.100${NC}"
        echo -e "         ${BLUE}export SERVER_USER=ubuntu${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ SSH connection verified${NC}"

    # Execute deployment on remote server
    echo -e "\n${BLUE}Executing remote deployment...${NC}"
    ssh "$SERVER_USER@$SERVER_HOST" bash <<'ENDSSH'
        set -e
        cd /opt/payment-webhook

        echo "📥 Pulling latest changes..."
        git fetch origin main

        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)

        if [ "$LOCAL" = "$REMOTE" ]; then
            echo "✅ Already up to date!"
        else
            echo "🔄 New changes detected, updating..."

            # Create backup
            BACKUP_DIR="/opt/payment-webhook-backups"
            mkdir -p $BACKUP_DIR
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            echo "📦 Creating backup: backup_$TIMESTAMP"
            tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" --exclude='venv' --exclude='.git' --exclude='*.log' . 2>/dev/null || true

            # Keep only last 5 backups
            ls -t $BACKUP_DIR/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm 2>/dev/null || true

            # Pull changes
            git reset --hard origin/main

            # Check if requirements changed
            if git diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -q "requirements.txt"; then
                echo "📚 Requirements changed, updating dependencies..."
                /opt/payment-webhook/venv/bin/pip install -r requirements.txt --quiet
            fi

            # Restart the service
            echo "♻️  Restarting webhook-receiver service..."
            sudo systemctl restart webhook-receiver.service

            # Wait for service to start
            sleep 3

            # Check service status
            if sudo systemctl is-active --quiet webhook-receiver.service; then
                echo "✅ Service restarted successfully!"
                NEW_VERSION=$(git rev-parse --short HEAD)
                echo "📌 Deployed version: $NEW_VERSION"
            else
                echo "❌ Service failed to start! Rolling back..."
                git reset --hard HEAD@{1}
                sudo systemctl restart webhook-receiver.service
                echo "🔙 Rolled back to previous version"
                exit 1
            fi
        fi

        echo "🎉 Deployment completed successfully!"
ENDSSH

    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✅ Deployment successful!${NC}"
    else
        echo -e "\n${RED}❌ Deployment failed!${NC}"
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    echo -e "\n${BLUE}🔍 Verifying deployment...${NC}"

    ssh "$SERVER_USER@$SERVER_HOST" bash <<'ENDSSH'
        # Check service status
        if sudo systemctl is-active --quiet webhook-receiver.service; then
            echo "✅ webhook-receiver service is running"
        else
            echo "❌ webhook-receiver service is not running"
            sudo systemctl status webhook-receiver.service
        fi

        # Check recent logs
        echo ""
        echo "📋 Recent logs (last 10 lines):"
        sudo journalctl -u webhook-receiver.service -n 10 --no-pager

        # Verify cooldown change
        echo ""
        if grep -q "1440 minutes" /opt/payment-webhook/payment_monitor.py; then
            echo "✅ Cooldown updated to 24 hours (1440 minutes)"
        else
            echo "⚠️  Cooldown change not found"
        fi

        # Verify log directory change
        if grep -q "./logs/webhook_receiver.log" /opt/payment-webhook/webhook_app.py; then
            echo "✅ Log directory updated to ./logs"
        else
            echo "⚠️  Log directory change not found"
        fi
ENDSSH
}

# Main execution
main() {
    cd "$PROJECT_DIR"

    echo -e "${BLUE}Step 1: Checking directory${NC}"
    check_directory

    echo -e "\n${BLUE}Step 2: Checking git status${NC}"
    check_git_status

    echo -e "\n${BLUE}Step 3: Pushing to GitHub${NC}"
    push_to_github

    echo -e "\n${BLUE}Step 4: Deploying to server${NC}"

    # Check if server credentials are set
    if [ "$SERVER_HOST" = "your-server-ip" ]; then
        echo -e "${YELLOW}⚠️  Server host not configured${NC}"
        read -p "Enter server hostname or IP: " SERVER_HOST
        read -p "Enter server username [root]: " SERVER_USER
        SERVER_USER=${SERVER_USER:-root}
    fi

    deploy_to_server

    echo -e "\n${BLUE}Step 5: Verifying deployment${NC}"
    verify_deployment

    echo -e "\n${GREEN}🎉 All done! Deployment completed successfully!${NC}"
}

# Run main function
main
