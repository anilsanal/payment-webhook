# Automated Deployment Guide

This guide explains how to automatically deploy changes from your local machine to the production server.

## 🚀 Quick Start

### One-Time Setup

#### Option 1: Using Personal Access Token (Easiest)

1. **Generate a GitHub Personal Access Token:**
   - Visit: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it a name: "Payment Webhook Deployment"
   - Select scope: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again)

2. **Configure macOS Keychain:**
   ```bash
   git push origin main
   ```
   - When prompted for username: enter your GitHub username
   - When prompted for password: paste your Personal Access Token
   - macOS Keychain will save it automatically

3. **Configure server details:**
   ```bash
   cd /Users/anil/Projects/payment-webhook
   cp .deploy-config .deploy-config.local
   nano .deploy-config.local
   ```
   Update with your server details:
   ```bash
   SERVER_HOST=your-server-ip
   SERVER_USER=root
   ```

#### Option 2: Using SSH Keys (Recommended for Long-term)

1. **Generate SSH key (if you don't have one):**
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   # Press Enter to accept default location
   # Optionally add a passphrase
   ```

2. **Add SSH key to GitHub:**
   ```bash
   # Copy public key
   cat ~/.ssh/id_ed25519.pub | pbcopy
   ```
   - Visit: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the key and save

3. **Switch Git remote to SSH:**
   ```bash
   cd /Users/anil/Projects/payment-webhook
   git remote set-url origin git@github.com:anilsanal/payment-webhook.git
   ```

4. **Test SSH connection:**
   ```bash
   ssh -T git@github.com
   # Should see: "Hi anilsanal! You've successfully authenticated..."
   ```

5. **Configure server SSH access:**
   ```bash
   # Test server connection
   ssh root@your-server-ip

   # If successful, update config
   nano .deploy-config.local
   ```

## 📦 Deployment Scripts

### 1. Quick Push (GitHub only)

Push changes to GitHub without deploying to server:

```bash
./quick_push.sh
```

This script:
- ✅ Shows uncommitted changes
- ✅ Pushes to GitHub
- ✅ Shows helpful error messages if authentication fails

### 2. Automated Full Deployment

Complete deployment from local → GitHub → server:

```bash
./auto_deploy.sh
```

Or with custom server:
```bash
export SERVER_HOST=192.168.1.100
export SERVER_USER=ubuntu
./auto_deploy.sh
```

This script:
- ✅ Checks for uncommitted changes
- ✅ Pushes to GitHub
- ✅ Deploys to server
- ✅ Creates backup before deployment
- ✅ Restarts services
- ✅ Verifies deployment
- ✅ Automatic rollback on failure

### 3. Manual Deployment (if automated fails)

```bash
# Step 1: Push to GitHub
git push origin main

# Step 2: SSH to server
ssh root@your-server

# Step 3: Run server-side deployment
cd /opt/payment-webhook
./deploy.sh
```

## 🔧 Configuration

### Server Configuration

Create `.deploy-config.local` (not tracked in git):

```bash
SERVER_HOST=192.168.1.100
SERVER_USER=root
SERVER_PORT=22
```

Or use environment variables:
```bash
export SERVER_HOST=payment.example.com
export SERVER_USER=ubuntu
./auto_deploy.sh
```

## 📋 What Gets Deployed

The deployment includes:

- ✅ Updated Python scripts (`payment_monitor.py`, `webhook_app.py`, etc.)
- ✅ Configuration changes
- ✅ Database migrations (if any)
- ✅ Updated dependencies (if requirements.txt changed)
- ❌ `.env` files (not tracked in git)
- ❌ Virtual environment (not tracked in git)
- ❌ Log files (not tracked in git)

## 🔍 Verification

After deployment, the script automatically verifies:

1. **Service Status:**
   - webhook-receiver service is running
   - Recent logs show no errors

2. **Code Changes:**
   - Cooldown updated to 1440 minutes
   - Log directory updated to ./logs

3. **Version:**
   - Shows deployed git commit hash

Manual verification commands:
```bash
# Check service status
ssh root@server "sudo systemctl status webhook-receiver.service"

# Check recent logs
ssh root@server "sudo journalctl -u webhook-receiver.service -n 50"

# Verify specific changes
ssh root@server "grep '1440 minutes' /opt/payment-webhook/payment_monitor.py"
```

## 🆘 Troubleshooting

### Authentication Failed (GitHub)

**Error:** `fatal: could not read Username for 'https://github.com'`

**Solution:**
1. Generate Personal Access Token (see Option 1 above)
2. Or switch to SSH (see Option 2 above)

### Cannot Connect to Server

**Error:** `ssh: connect to host ... port 22: Connection refused`

**Solutions:**
1. Check server IP/hostname: `ping your-server-ip`
2. Check SSH is running: `ssh -v root@your-server-ip`
3. Check firewall allows SSH (port 22)
4. Verify credentials in `.deploy-config.local`

### Service Failed to Start

**Error:** `Service failed to start! Rolling back...`

**What happens:**
- Automatic rollback to previous version
- Service restarted with old code

**Next steps:**
1. Check logs: `ssh root@server "sudo journalctl -u webhook-receiver.service -n 100"`
2. Check syntax errors: `ssh root@server "cd /opt/payment-webhook && ./venv/bin/python -m py_compile webhook_app.py"`
3. Fix issues locally and redeploy

### Deployment Hangs

**Issue:** Script appears stuck

**Solutions:**
1. Check SSH connection: `ssh root@your-server-ip echo "test"`
2. Check git fetch: `ssh root@server "cd /opt/payment-webhook && git fetch"`
3. Cancel (Ctrl+C) and try manual deployment

## 📝 Best Practices

1. **Always test locally first:**
   ```bash
   cd /Users/anil/Projects/payment-webhook
   ./venv/bin/python payment_monitor.py
   ```

2. **Commit with descriptive messages:**
   ```bash
   git commit -m "Fix: Update cooldown to 24 hours"
   ```

3. **Deploy during low-traffic periods** (if possible)

4. **Monitor after deployment:**
   ```bash
   ssh root@server "tail -f /var/log/payment_monitor.log"
   ```

5. **Keep backups:** Deployment script automatically keeps last 5 backups

## 🔐 Security Notes

- ✅ `.deploy-config.local` is in `.gitignore` (safe for credentials)
- ✅ Personal Access Tokens stored in macOS Keychain (encrypted)
- ✅ SSH keys are password-protected (recommended)
- ❌ Never commit `.env` files
- ❌ Never commit credentials to git

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Push to GitHub | `./quick_push.sh` |
| Full deployment | `./auto_deploy.sh` |
| Check service | `ssh root@server "systemctl status webhook-receiver"` |
| View logs | `ssh root@server "tail -f /var/log/payment_monitor.log"` |
| Manual deploy | `ssh root@server "cd /opt/payment-webhook && ./deploy.sh"` |
| Rollback | Automatic on failure, or restore from `/opt/payment-webhook-backups/` |

## 🆘 Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review deployment logs
3. Test SSH and Git connections separately
4. Try manual deployment steps

---

**Last Updated:** 2025-11-11
