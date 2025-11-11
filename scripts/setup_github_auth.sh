#!/bin/bash
# Interactive script to setup GitHub authentication

echo "🔐 GitHub Authentication Setup"
echo "=============================="
echo ""
echo "Choose your authentication method:"
echo ""
echo "1. Personal Access Token (HTTPS) - Easiest, works immediately"
echo "2. SSH Keys - Best for long-term automation"
echo "3. Skip (manual setup)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📝 Setting up Personal Access Token..."
        echo ""
        echo "Step 1: Generate token"
        echo "  → Opening GitHub token page..."
        sleep 2
        open "https://github.com/settings/tokens/new?description=Payment-Webhook-Deployment&scopes=repo"
        echo ""
        echo "  ✓ Create a new token with 'repo' scope"
        echo "  ✓ Copy the token (you'll only see it once)"
        echo ""
        read -p "Press Enter when you have copied the token..."
        echo ""
        echo "Step 2: Test authentication"
        echo "  → Attempting push to GitHub..."
        echo "  → You'll be prompted for username and password"
        echo "  → Username: your GitHub username"
        echo "  → Password: paste your Personal Access Token"
        echo ""
        read -p "Press Enter to continue..."

        cd /Users/anil/Projects/payment-webhook
        git push origin main

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Authentication successful!"
            echo "✅ Token saved to macOS Keychain"
            echo ""
            echo "You can now use ./auto_deploy.sh for automated deployments"
        else
            echo ""
            echo "❌ Authentication failed"
            echo "Please try again or choose option 2 (SSH)"
        fi
        ;;

    2)
        echo ""
        echo "🔑 Setting up SSH Keys..."
        echo ""

        # Check if SSH key exists
        if [ -f ~/.ssh/id_ed25519.pub ] || [ -f ~/.ssh/id_rsa.pub ]; then
            echo "✓ SSH key found"

            if [ -f ~/.ssh/id_ed25519.pub ]; then
                SSH_KEY=$(cat ~/.ssh/id_ed25519.pub)
            else
                SSH_KEY=$(cat ~/.ssh/id_rsa.pub)
            fi
        else
            echo "Step 1: Generate SSH key"
            read -p "Enter your email: " email
            ssh-keygen -t ed25519 -C "$email"
            SSH_KEY=$(cat ~/.ssh/id_ed25519.pub)
        fi

        echo ""
        echo "Step 2: Copy SSH key to clipboard"
        echo "$SSH_KEY" | pbcopy
        echo "✓ SSH key copied to clipboard"
        echo ""

        echo "Step 3: Add to GitHub"
        echo "  → Opening GitHub SSH keys page..."
        sleep 2
        open "https://github.com/settings/ssh/new"
        echo ""
        echo "  ✓ Paste the key (already in clipboard)"
        echo "  ✓ Give it a title: 'Mac - Payment Webhook'"
        echo "  ✓ Click 'Add SSH key'"
        echo ""
        read -p "Press Enter when you've added the key to GitHub..."

        echo ""
        echo "Step 4: Test SSH connection"
        ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"

        if [ $? -eq 0 ]; then
            echo "✅ SSH connection successful"

            echo ""
            echo "Step 5: Switch git remote to SSH"
            cd /Users/anil/Projects/payment-webhook
            git remote set-url origin git@github.com:anilsanal/payment-webhook.git
            echo "✓ Remote updated to SSH"

            echo ""
            echo "Step 6: Test push"
            git push origin main

            if [ $? -eq 0 ]; then
                echo ""
                echo "✅ Setup complete! SSH authentication working"
                echo ""
                echo "You can now use ./auto_deploy.sh for automated deployments"
            fi
        else
            echo "❌ SSH connection failed"
            echo "Please check the key was added correctly to GitHub"
        fi
        ;;

    3)
        echo ""
        echo "Setup skipped. You can:"
        echo "  - Run this script again: ./setup_github_auth.sh"
        echo "  - Follow manual steps in DEPLOYMENT.md"
        echo "  - Use: git push origin main (will prompt for auth)"
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Setup complete!"
