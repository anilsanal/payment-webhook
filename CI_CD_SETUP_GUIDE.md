# CI/CD Setup Guide - Payment Webhook System

This guide will help you complete the GitHub Actions CI/CD setup for automatic deployments.

## ✅ What's Already Done

- ✅ Git repository initialized
- ✅ .gitignore configured (excludes .env and sensitive files)
- ✅ GitHub Actions workflow created
- ✅ Deployment script with automatic rollback
- ✅ SSH key pair generated
- ✅ Initial commit created

## 🔧 What You Need to Do (15 minutes)

### Step 1: Create GitHub Repository (5 minutes)

1. Go to https://github.com/new
2. Create a **private repository** named: `payment-webhook` (or any name you prefer)
3. **Important:** Do NOT initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

### Step 2: Push Code to GitHub (2 minutes)

Run these commands on your server:

```bash
cd /opt/payment-webhook

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/payment-webhook.git

# Push code to GitHub
git push -u origin main
```

You'll be prompted for your GitHub credentials. If you have 2FA enabled, use a Personal Access Token instead of password:
- Go to: https://github.com/settings/tokens
- Generate new token (classic)
- Select scope: `repo` (Full control of private repositories)
- Copy the token and use it as password

### Step 3: Configure GitHub Secrets (5 minutes)

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these 4 secrets:

#### Secret 1: SSH_PRIVATE_KEY
```bash
# On your server, run this to get the private key:
cat /root/.ssh/github_deploy
```
Copy the entire output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

**Name:** `SSH_PRIVATE_KEY`
**Value:** Paste the private key

#### Secret 2: SSH_HOST
This is your server's IP address or domain.

**Name:** `SSH_HOST`
**Value:** Your server IP (e.g., `webhook.polpay.pro` or the IP address)

#### Secret 3: SSH_USER
The user for SSH connection (currently using root).

**Name:** `SSH_USER`
**Value:** `root`

#### Secret 4: WEBHOOK_URL
The public URL for health checks.

**Name:** `WEBHOOK_URL`
**Value:** `https://webhook.polpay.pro`

### Step 4: Test Your Setup (3 minutes)

1. Make a small test change to verify CI/CD works:

```bash
cd /opt/payment-webhook
echo "# CI/CD is working!" >> TEST.md
git add TEST.md
git commit -m "Test CI/CD deployment"
git push
```

2. Watch the deployment:
   - Go to your GitHub repository
   - Click **Actions** tab
   - You should see your workflow running
   - Watch the logs in real-time

3. If successful, you'll see ✅ next to the workflow

## 🎯 How to Use CI/CD

### Automatic Deployment (Recommended)
Simply push to the main branch:
```bash
cd /opt/payment-webhook
git add .
git commit -m "Your change description"
git push
```

The workflow automatically:
1. Pulls latest code
2. Updates dependencies (if requirements.txt changed)
3. Restarts service
4. Runs health check
5. Rolls back if anything fails

### Manual Deployment
1. Go to GitHub repository → **Actions**
2. Click **Deploy to Production** workflow
3. Click **Run workflow** → **Run workflow**

## 📊 Monitoring Deployments

### View Deployment Logs
- GitHub repository → **Actions** tab
- Click on any workflow run to see detailed logs

### Check Service Status on Server
```bash
# Check if service is running
systemctl status webhook-receiver.service

# View recent logs
tail -f /var/log/webhook_receiver.log

# Check current git version
cd /opt/payment-webhook && git log -1 --oneline
```

### Health Check
```bash
curl https://webhook.polpay.pro/health
```

## 🔄 Deployment Process Explained

```
You: git push
    ↓
GitHub Actions triggers
    ↓
Connects to server via SSH
    ↓
Creates backup (kept last 5)
    ↓
Pulls latest code
    ↓
Updates dependencies (if needed)
    ↓
Restarts webhook-receiver service
    ↓
Health check /health endpoint
    ↓
✅ Success OR ❌ Automatic rollback
```

## 🔐 Security Notes

- ✅ SSH key is used (more secure than password)
- ✅ .env file stays on server (never in Git)
- ✅ Private repository recommended
- ✅ GitHub Secrets are encrypted
- ✅ Only root user can deploy

## 🆘 Troubleshooting

### Deployment fails with SSH error
```bash
# Verify SSH key is in authorized_keys
cat /root/.ssh/authorized_keys | grep github-actions-deploy
```

### Service fails to restart
```bash
# Check service logs
journalctl -u webhook-receiver.service -n 50

# Manually restart
systemctl restart webhook-receiver.service
```

### Health check fails
```bash
# Check if service is listening
netstat -tlnp | grep 8000

# Check NGINX
systemctl status nginx
```

### Rollback to previous version manually
```bash
cd /opt/payment-webhook
git log --oneline  # Find the commit hash you want
git reset --hard COMMIT_HASH
systemctl restart webhook-receiver.service
```

## 📈 Next Steps (Optional)

1. **Add automated testing**
   - Create `tests/` directory
   - Add pytest to requirements.txt
   - Update workflow to run tests before deploy

2. **Add notifications**
   - Telegram/Slack notification on deployment
   - Email alerts on failures

3. **Create staging environment**
   - Add `staging` branch
   - Separate workflow for staging

4. **Add database migrations**
   - Include migration checks in deploy.sh
   - Run migrations before restart

## 📝 Quick Reference

```bash
# Check what will be committed
git status

# Stage all changes
git add -A

# Commit with message
git commit -m "Description of changes"

# Push to trigger deployment
git push

# View commit history
git log --oneline -10

# Undo last commit (not pushed)
git reset --soft HEAD~1
```

## ✨ Benefits You Now Have

✅ Automatic deployments on every push
✅ Automated health checks
✅ Automatic rollback on failure
✅ Backup before each deployment
✅ Version control (track all changes)
✅ Easy rollback to any previous version
✅ Deployment logs and history
✅ Manual deployment option

---

**Need help?** Check the deployment logs in GitHub Actions or run `systemctl status webhook-receiver.service` on the server.
