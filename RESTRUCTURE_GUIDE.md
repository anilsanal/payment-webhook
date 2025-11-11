# Project Restructuring - Complete Execution Guide

## 🎯 Goal

Reorganize the payment-webhook project from flat structure (46 files in root) to organized folder structure WITHOUT affecting the running production server.

## ⚠️ CRITICAL: Two-Phase Approach

### Phase 1: LOCAL (Safe, No Production Impact)
- Run migration scripts locally
- Test changes
- Commit to GitHub
- **Production server is NOT affected yet**

### Phase 2: PRODUCTION (After testing)
- Pull changes on server
- Update systemd service
- Update cron job
- Restart services
- Verify

## 📋 Pre-Flight Checklist

Before starting:

- [ ] Backup exists (automatic during migration)
- [ ] Git working directory is clean
- [ ] You understand rollback procedure
- [ ] You have SSH access to production server
- [ ] Production server is currently running fine

## 🚀 PHASE 1: Local Restructuring

### Step 1: Make scripts executable

```bash
cd /Users/anil/Documents/GitHub/payment-webhook

chmod +x migrate_structure.sh
chmod +x update_imports.sh
chmod +x rollback_structure.sh
chmod +x update_production.sh
```

### Step 2: Run migration script

```bash
./migrate_structure.sh
```

**What this does:**
- ✅ Creates automatic backup (../payment-webhook-backup-TIMESTAMP)
- ✅ Creates new folder structure
- ✅ Moves all files to appropriate folders
- ✅ Creates Python package files (__init__.py)
- ✅ Makes scripts executable

**Expected output:**
```
════════════════════════════════════════════════════════════
   Payment Webhook - Project Structure Migration
════════════════════════════════════════════════════════════

Current directory: /Users/anil/Documents/GitHub/payment-webhook

STEP 1: Creating backup
────────────────────────────────────────────────────────────
✓ Backup created: ../payment-webhook-backup-20250111_123456

STEP 2: Creating folder structure
────────────────────────────────────────────────────────────
✓ Folders created

STEP 3: Moving files (copying first for safety)
────────────────────────────────────────────────────────────
  → Moving application code...
  → Moving services...
  → Moving utilities...
  → Moving database files...
  → Moving data files...
  → Moving scripts...
  → Moving documentation...
✓ Files moved

STEP 4: Creating __init__.py files
────────────────────────────────────────────────────────────
✓ Python package files created

STEP 5: Making scripts executable
────────────────────────────────────────────────────────────
✓ Scripts made executable

════════════════════════════════════════════════════════════
✅ MIGRATION COMPLETE!
════════════════════════════════════════════════════════════
```

### Step 3: Verify structure

```bash
# Check new structure
ls -la

# Should see:
# app/
# services/
# utils/
# database/
# data/
# scripts/
# tests/
# docs/
# README.md
# requirements.txt
# .gitignore
# .env.example

# Verify key files exist
ls -la app/webhook_app.py
ls -la services/payment_monitor.py
ls -la scripts/deploy.sh
```

### Step 4: Update imports (if needed)

```bash
./update_imports.sh
```

**What this does:**
- Checks Python files for hardcoded paths
- Updates any references to CSV files or other resources
- Most files don't need changes (they're standalone)

### Step 5: Test locally

**Test 1: Check Python syntax**
```bash
# Activate venv
source venv/bin/activate

# Test main app imports
python3 -c "from app.webhook_app import app; print('✓ webhook_app imports OK')"

# Test monitor imports
python3 -c "from services.payment_monitor import main; print('✓ payment_monitor imports OK')"
```

**Test 2: Start application locally**
```bash
# Start webhook receiver
python3 -m uvicorn app.webhook_app:app --reload --port 8000

# In another terminal, test endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected"}
```

**Test 3: Check scripts**
```bash
# Verify deploy script exists and is executable
ls -la scripts/deploy.sh

# Check script can be found
bash scripts/deploy.sh --help 2>&1 | head -5
```

### Step 6: Review changes

```bash
# See what changed
git status

# Should show:
# - Deleted: all files from root (moved to folders)
# - New: all folders and files in new locations
# - New: README.md, .env.example, migration scripts

# Review file moves
git diff --summary
```

### Step 7: Commit changes

```bash
# Add all changes
git add .

# Commit with clear message
git commit -m "Restructure: Organize project into logical folders

- Move app code to app/, services/, utils/
- Organize database files into database/ subdirectories
- Move documentation to docs/ with categorization
- Move deployment scripts to scripts/
- Add comprehensive README.md
- Add .env.example template
- Update all file references

NO PRODUCTION IMPACT: This only reorganizes local structure.
Production update requires separate deployment (Phase 2).

Structure:
- app/          Main application code
- services/     Background services (monitor, reports)
- utils/        One-time utility scripts
- database/     SQL files (schema, migrations, views)
- data/         Static data files
- scripts/      Deployment automation
- tests/        Test suite (prepared)
- docs/         All documentation organized"

# Verify commit
git log -1 --stat
```

### Step 8: Push to GitHub

```bash
# Push to main branch
git push origin main

# Verify on GitHub
# Check that files are in correct folders
```

**🎉 PHASE 1 COMPLETE!**

At this point:
- ✅ Local structure is reorganized
- ✅ Changes committed to GitHub
- ✅ CI/CD will run but won't deploy yet (needs Phase 2)
- ✅ Production server is still running with old structure
- ✅ No production impact whatsoever

---

## 🏭 PHASE 2: Production Deployment

**⚠️ IMPORTANT: Only proceed after Phase 1 is complete and tested!**

### Before You Start

1. **Verify CI/CD didn't auto-deploy:**
   ```bash
   # Check GitHub Actions
   # Make sure auto-deployment is not enabled or completed
   ```

2. **Check production is healthy:**
   ```bash
   ssh user@your-server 'sudo systemctl status webhook-receiver'
   curl https://your-domain/health
   ```

3. **Have rollback plan ready:**
   - Know how to SSH to server
   - Have previous commit hash ready
   - Understand rollback procedure

### Step 1: SSH to production server

```bash
ssh user@your-production-server
cd /opt/payment-webhook
```

### Step 2: Pull changes from GitHub

```bash
# Fetch latest
git fetch origin main

# Check what will change
git log HEAD..origin/main --oneline

# Show file changes
git diff HEAD..origin/main --stat

# Pull changes
git pull origin main
```

### Step 3: Verify new structure on server

```bash
# Check structure is correct
ls -la app/
ls -la services/
ls -la scripts/

# Verify key files
ls -la app/webhook_app.py
ls -la services/payment_monitor.py
```

### Step 4: Run production update script

```bash
# Make script executable
chmod +x update_production.sh

# Run update script (THIS UPDATES PRODUCTION)
sudo ./update_production.sh
```

**What this does:**
1. Creates backup of systemd service and crontab
2. Updates systemd ExecStart line: `webhook_app:app` → `app.webhook_app:app`
3. Reloads systemd daemon
4. Updates cron job path: `payment_monitor.py` → `services/payment_monitor.py`
5. Restarts webhook-receiver service
6. Runs health check
7. Auto-rollback if health check fails

**Expected output:**
```
════════════════════════════════════════════════════════════
   Production Server - Structure Update (Phase 2)
════════════════════════════════════════════════════════════

Current directory: /opt/payment-webhook

STEP 1: Creating backup
────────────────────────────────────────────────────────────
✓ Backup created: /opt/payment-webhook-prod-backup-20250111_123456
  - systemd service file backed up
  - crontab backed up

STEP 2: Updating systemd service
────────────────────────────────────────────────────────────
Updating /etc/systemd/system/webhook-receiver.service
✓ Systemd service updated successfully

New ExecStart line:
ExecStart=/opt/payment-webhook/venv/bin/python -m uvicorn app.webhook_app:app --host 0.0.0.0 --port 8000 --log-level info

STEP 3: Reloading systemd
────────────────────────────────────────────────────────────
✓ Systemd daemon reloaded

STEP 4: Updating cron job
────────────────────────────────────────────────────────────
✓ Cron job updated successfully

New cron job:
*/5 * * * * /opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/services/payment_monitor.py >> /var/log/payment_monitor.log 2>&1

STEP 5: Restarting webhook service
────────────────────────────────────────────────────────────
Stopping service...
Starting service with new structure...
✓ Service restarted successfully!

Service status:
● webhook-receiver.service - Payment Gateway Webhook Receiver
     Loaded: loaded (/etc/systemd/system/webhook-receiver.service; enabled; vendor preset: enabled)
     Active: active (running) since [timestamp]

STEP 6: Testing webhook endpoint
────────────────────────────────────────────────────────────
Waiting 5 seconds for service to be fully ready...
✓ Health check passed!

{
  "status": "healthy",
  "database": "connected"
}

════════════════════════════════════════════════════════════
✅ PRODUCTION UPDATE COMPLETE!
════════════════════════════════════════════════════════════
```

### Step 5: Verify production is working

```bash
# Check service is running
sudo systemctl status webhook-receiver

# Watch logs in real-time
sudo journalctl -u webhook-receiver.service -f

# In another terminal: Check health endpoint
curl http://localhost:8000/health

# Check main endpoint
curl http://localhost:8000/

# Verify webhook can receive (if you have test webhook)
curl -X POST http://localhost:8000/webhook \
  -d "trans_order=TEST&reply_code=000&merchant_id=1"
```

### Step 6: Monitor for a few minutes

```bash
# Watch application logs
tail -f /var/log/webhook_receiver.log

# Wait for next cron run (within 5 minutes)
tail -f /var/log/payment_monitor.log

# Check for any errors
sudo journalctl -u webhook-receiver.service -n 100 | grep -i error
```

### Step 7: Test Telegram alerts (optional)

```bash
# Manually trigger monitor
cd /opt/payment-webhook
source venv/bin/activate
python3 services/payment_monitor.py

# Check output
```

**🎉 PHASE 2 COMPLETE!**

Production server is now running with new structure!

---

## 🔙 ROLLBACK PROCEDURES

### If Something Goes Wrong During Phase 1 (Local)

**Option 1: Git reset**
```bash
cd /Users/anil/Documents/GitHub/payment-webhook
git reset --hard HEAD~1
```

**Option 2: Use rollback script**
```bash
./rollback_structure.sh
```

**Option 3: Restore from backup**
```bash
# Find backup
ls -la ../payment-webhook-backup-*

# Copy backup
cd ..
rm -rf payment-webhook
cp -r payment-webhook-backup-TIMESTAMP payment-webhook
cd payment-webhook
```

### If Something Goes Wrong During Phase 2 (Production)

**Automatic rollback:**
- The `update_production.sh` script automatically rolls back if health check fails

**Manual rollback:**

```bash
# SSH to server
ssh user@your-server
cd /opt/payment-webhook

# Reset git
git reset --hard <previous-commit-hash>

# Restore systemd service
sudo cp /opt/payment-webhook-prod-backup-TIMESTAMP/webhook-receiver.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restore crontab
crontab /opt/payment-webhook-prod-backup-TIMESTAMP/crontab.backup

# Restart service
sudo systemctl restart webhook-receiver
```

**Verify rollback:**
```bash
sudo systemctl status webhook-receiver
curl http://localhost:8000/health
tail -f /var/log/webhook_receiver.log
```

---

## ✅ Post-Migration Verification Checklist

### Local Verification
- [ ] New folder structure exists
- [ ] All files are in correct folders
- [ ] Python imports work (`python3 -c "from app.webhook_app import app"`)
- [ ] Scripts are executable
- [ ] Git commit is clean
- [ ] Changes pushed to GitHub

### Production Verification
- [ ] Git pull successful
- [ ] New structure exists on server
- [ ] Systemd service updated
- [ ] Cron job updated
- [ ] Service is running (`systemctl status webhook-receiver`)
- [ ] Health check passes
- [ ] No errors in logs
- [ ] Monitor ran successfully (check within 5 min)
- [ ] Webhooks are being received
- [ ] Database writes working
- [ ] Telegram alerts working (if tested)
- [ ] Grafana dashboards still working

---

## 📊 What Changed - Quick Reference

### Systemd Service Change
**Before:**
```
ExecStart=/opt/payment-webhook/venv/bin/python -m uvicorn webhook_app:app
```

**After:**
```
ExecStart=/opt/payment-webhook/venv/bin/python -m uvicorn app.webhook_app:app
```

### Cron Job Change
**Before:**
```
*/5 * * * * /opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/payment_monitor.py
```

**After:**
```
*/5 * * * * /opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/services/payment_monitor.py
```

### File Locations

| Before | After |
|--------|-------|
| `webhook_app.py` | `app/webhook_app.py` |
| `payment_monitor.py` | `services/payment_monitor.py` |
| `bin_import.py` | `utils/bin_import.py` |
| `deploy.sh` | `scripts/deploy.sh` |
| `DEPLOYMENT.md` | `docs/setup/DEPLOYMENT.md` |
| `database_schema.sql` | `database/schema/database_schema.sql` |
| `BINS_and_BANKS_List.csv` | `data/BINS_and_BANKS_List.csv` |

### What Stayed the Same
- `.env` file location (still in `/opt/payment-webhook/.env`)
- Database connection (unchanged)
- API endpoints (unchanged)
- Webhook URL (unchanged)
- All functionality (100% same)

---

## 🆘 Troubleshooting

### "Service failed to start"

```bash
# Check detailed error
sudo journalctl -u webhook-receiver.service -n 50

# Common issues:
# 1. Module not found → Check import path in systemd
# 2. Permission denied → Check file ownership
# 3. Port in use → Check if old process is running

# Fix: Verify systemd service file
sudo cat /etc/systemd/system/webhook-receiver.service | grep ExecStart
# Should show: app.webhook_app:app
```

### "Health check failed"

```bash
# Check if service is actually running
sudo systemctl status webhook-receiver

# Check what port is listening
sudo lsof -i :8000

# Check database connection
psql -U webhook_user -d payment_transactions -c "SELECT 1"

# View recent logs
tail -50 /var/log/webhook_receiver.log
```

### "Cron job not running"

```bash
# Check crontab
crontab -l | grep payment_monitor

# Check path is correct
ls -la /opt/payment-webhook/services/payment_monitor.py

# Manually run monitor
cd /opt/payment-webhook
source venv/bin/activate
python3 services/payment_monitor.py

# Check for errors
tail -f /var/log/payment_monitor.log
```

### "Import errors"

```bash
# Verify Python can find modules
cd /opt/payment-webhook
source venv/bin/activate

# Test imports
python3 -c "import sys; sys.path.insert(0, '.'); from app.webhook_app import app; print('OK')"

# Check PYTHONPATH
echo $PYTHONPATH

# If needed, add to systemd service:
# Environment="PYTHONPATH=/opt/payment-webhook"
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `tail -f /var/log/webhook_receiver.log`
2. Check service: `sudo systemctl status webhook-receiver`
3. Check recent changes: `git log -3 --oneline`
4. Rollback if needed (see Rollback Procedures above)
5. Contact system administrator

---

## 📝 Notes

- **Total migration time**: 30-60 minutes (including testing)
- **Production downtime**: ~30 seconds (service restart only)
- **Risk level**: LOW (automatic backups + rollback)
- **Reversible**: YES (multiple rollback options)
- **Testing required**: YES (Phase 1 must be tested locally first)

---

**Last Updated**: 2025-01-11
**Migration Status**: Ready for execution
**Tested**: Locally ✅ | Production ⏳
