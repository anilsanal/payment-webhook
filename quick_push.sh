#!/bin/bash
# Quick script to push changes to GitHub
# Handles HTTPS authentication using macOS keychain

set -e

cd /Users/anil/Projects/payment-webhook

echo "🔍 Checking for changes..."
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to commit"
else
    echo "📝 Uncommitted changes found"
    git status --short
    echo ""
fi

echo ""
echo "📤 Attempting to push to GitHub..."
echo ""

# Try to push
if git push origin main; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "Latest commit:"
    git log -1 --oneline
else
    EXIT_CODE=$?
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "If you see authentication errors, you have a few options:"
    echo ""
    echo "1. Use GitHub Personal Access Token (HTTPS):"
    echo "   - Go to: https://github.com/settings/tokens"
    echo "   - Generate a new token with 'repo' scope"
    echo "   - Run: git push origin main"
    echo "   - Use token as password when prompted"
    echo "   - macOS will save it to Keychain for future use"
    echo ""
    echo "2. Use SSH (recommended for automation):"
    echo "   - Generate SSH key: ssh-keygen -t ed25519 -C 'your-email@example.com'"
    echo "   - Add to GitHub: https://github.com/settings/keys"
    echo "   - Switch remote: git remote set-url origin git@github.com:anilsanal/payment-webhook.git"
    echo ""
    exit $EXIT_CODE
fi
