# Project Restructuring Migration Plan

## Overview
Safe migration from flat structure to organized folder structure WITHOUT affecting production server.

## Strategy: Two-Phase Deployment

### Phase 1: LOCAL REORGANIZATION (This PR)
- Reorganize files into folders
- Update all import paths
- Update documentation
- Test locally
- Commit to GitHub

### Phase 2: SERVER UPDATE (Separate deployment)
- Pull changes to production
- Update systemd service file
- Update cron job
- Restart services
- Verify everything works

## Safety Measures

1. ✅ Backup before any changes
2. ✅ Git commit after each major step
3. ✅ Keep all files (no deletions)
4. ✅ Test locally before pushing
5. ✅ Rollback script ready
6. ✅ Production update is separate step

## Files That Stay in Root

These files MUST stay in root directory:
- `.env` (production only)
- `.gitignore`
- `requirements.txt`
- `README.md`
- `.deploy-config`

## Files Changed on Production Server

When we deploy Phase 2, these need updates:

1. **Systemd Service** `/etc/systemd/system/webhook-receiver.service`:
   - Change: `webhook_app:app` → `app.webhook_app:app`

2. **Crontab** for monitoring:
   - Change: `/opt/payment-webhook/payment_monitor.py`
   - To: `/opt/payment-webhook/services/payment_monitor.py`

3. **Environment file path** stays the same:
   - `/opt/payment-webhook/.env` (no change needed)

## Rollback Plan

If anything breaks:
```bash
cd /opt/payment-webhook
git reset --hard <previous-commit-hash>
sudo systemctl restart webhook-receiver
```

## Timeline

- **Today**: Local restructuring + testing (30-60 min)
- **Deploy Phase 2**: After local testing passes (10 min on server)
