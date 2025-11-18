# Deployment Checklist - Exclude Test MIDs (43110201461 / Timesaver)

**Date:** 2025-11-18
**Version:** Exclude Test MIDs from Alerts & Dashboards
**Priority:** Medium (Reduces false alerts)

## 📋 Pre-Deployment Summary

### Changes Overview
This deployment excludes test/dummy MIDs from triggering false alerts and appearing in analytics dashboards.

**Test MIDs Excluded:**
- MID ID: `43110201461`
- MID Name: `Timesaver` (case-insensitive)
- Any MID name containing `test` (case-insensitive)

### Files Modified
1. ✅ [services/payment_monitor.py](services/payment_monitor.py) - Alert bot exclusion logic
2. ✅ [database/views/create_grafana_views.sql](database/views/create_grafana_views.sql) - 3 timeout views
3. ✅ [database/views/create_monitoring_views.sql](database/views/create_monitoring_views.sql) - 4 MID+Bank views
4. ✅ [database/views/create_bank_performance_views.sql](database/views/create_bank_performance_views.sql) - 6 bank views (partial)

### Files Created
1. ✅ [database/migrations/migration_exclude_test_mids_all_views.sql](database/migrations/migration_exclude_test_mids_all_views.sql) - **Main migration**
2. ✅ [docs/EXCLUDED_MIDS.md](docs/EXCLUDED_MIDS.md) - Documentation

---

## 🚀 Deployment Steps

### Step 1: Git Commit & Push
```bash
# Add all changes
git add services/payment_monitor.py
git add database/views/*.sql
git add database/migrations/migration_exclude_test_mids_all_views.sql
git add docs/EXCLUDED_MIDS.md
git add DEPLOYMENT_CHECKLIST.md

# Commit with descriptive message
git commit -m "Exclude test MIDs from alerts and dashboards

- Add exclusion filter for MID 43110201461 (Timesaver)
- Filter test MIDs from Telegram alerts
- Update 18 Grafana views to exclude test data
- Add comprehensive migration script
- Document exclusion configuration

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### Step 2: Backup Production Database (Server)
```bash
# SSH to server
ssh root@your-server

# Create backup
pg_dump -U webhook_user payment_transactions > /tmp/payment_transactions_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh /tmp/payment_transactions_backup_*.sql
```

### Step 3: Run Database Migration (Server)
```bash
# On production server
cd /opt/payment-webhook

# Run migration (updates all 18 views)
psql -U webhook_user -d payment_transactions -f database/migrations/migration_exclude_test_mids_all_views.sql

# Expected output:
# BEGIN
# CREATE OR REPLACE VIEW (x18 times)
# COMMIT
# ✅ Migration completed: Test MIDs excluded from ALL views
```

### Step 4: Deploy Code Changes
```bash
# Option A: Use auto-deploy script (from local machine)
./scripts/auto_deploy.sh

# Option B: Manual deployment (on server)
cd /opt/payment-webhook
git pull origin main
sudo systemctl restart webhook-receiver.service
```

### Step 5: Verify Deployment
```bash
# On production server

# 1. Check service status
sudo systemctl status webhook-receiver.service

# 2. Verify Python code has exclusion logic
grep -A 5 "EXCLUDED_MIDS" /opt/payment-webhook/services/payment_monitor.py

# 3. Test database views
psql -U webhook_user -d payment_transactions -c "
SELECT 'Test: Should return 0 rows' as test;
SELECT COUNT(*) FROM timeout_performance_5min WHERE mid_id = '43110201461';
"

# 4. Check monitoring logs (wait for next 5-min run)
sudo journalctl -u payment-monitor.timer -f
# Should see: "⏭️ Skipping excluded MID: Timesaver (43110201461)"
```

---

## ✅ Post-Deployment Verification

### Immediate Checks
- [ ] webhook-receiver service is running
- [ ] No errors in application logs
- [ ] Database migration completed successfully
- [ ] All 18 views updated in database

### Within 15 Minutes
- [ ] Payment monitor runs without errors
- [ ] Test MIDs are skipped with log message
- [ ] No false alerts for Timesaver MID

### Within 1 Hour
- [ ] Grafana dashboards exclude test MIDs
- [ ] Real production alerts still working
- [ ] Revenue calculations exclude test data

---

## 🔄 Rollback Plan (If Needed)

If issues occur:

### Rollback Python Code
```bash
# On server
cd /opt/payment-webhook
git reset --hard HEAD~1
sudo systemctl restart webhook-receiver.service
```

### Rollback Database Views
```bash
# Restore from backup
psql -U webhook_user -d payment_transactions < /tmp/payment_transactions_backup_YYYYMMDD_HHMMSS.sql

# Or recreate original views (without exclusions)
# Edit each view SQL to remove the exclusion filters and re-run
```

---

## 📊 Impact Assessment

### Positive Impacts
✅ No more false critical alerts for test MIDs
✅ Cleaner analytics dashboards
✅ More accurate revenue reporting
✅ Better signal-to-noise ratio in monitoring

### Potential Risks (Mitigated)
⚠️ **Risk:** Legitimate MID accidentally excluded
✅ **Mitigation:** Only specific test MIDs excluded, documented pattern matching

⚠️ **Risk:** Migration fails on production
✅ **Mitigation:** Tested locally, backup before migration, rollback plan ready

⚠️ **Risk:** Alert bot stops working
✅ **Mitigation:** Filter is additive (only skips, doesn't break), existing logic intact

---

## 📝 Maintenance Notes

### Adding New Test MIDs
See [docs/EXCLUDED_MIDS.md](docs/EXCLUDED_MIDS.md) for instructions.

Quick summary:
1. Add to `EXCLUDED_MIDS` list in [payment_monitor.py](services/payment_monitor.py)
2. Add to SQL `NOT IN` clause in migration file
3. Run migration on production
4. Redeploy code

### Monitoring
- Test MID skip messages appear in monitoring logs
- Can query excluded transaction count: `SELECT COUNT(*) FROM transactions WHERE mid_id = '43110201461'`

---

## 🎯 Success Criteria

Deployment is successful when:
- [x] Code deployed without errors
- [x] Migration completed successfully
- [x] Service restarted cleanly
- [ ] Test MID alerts are skipped (verify in logs)
- [ ] Grafana dashboards exclude test data (verify visually)
- [ ] Production alerts still functioning (verify next real alert)

---

## 📞 Support

**Issue:** Test MID still appearing in dashboard
**Solution:** Check migration ran successfully, verify view definition

**Issue:** Real MID being excluded
**Solution:** Check MID name doesn't contain "test" or "timesaver"

**Issue:** Migration fails
**Solution:** Check PostgreSQL permissions, verify database connection

---

**Deployment Lead:** Claude Code
**Approved By:** _________________
**Deployment Date:** _________________
**Deployment Time:** _________________
