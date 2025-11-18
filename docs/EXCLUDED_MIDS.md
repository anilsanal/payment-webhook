# Excluded MIDs Configuration

## Overview
This document explains how test/dummy MIDs are excluded from monitoring alerts and Grafana dashboards to prevent false alarms.

## Problem
Test MIDs like "Timesaver" (MID: `43110201461`) were triggering production alerts and appearing in Grafana dashboards, creating noise and false alarms for the operations team.

## Solution
Implemented filtering at two levels:

### 1. Telegram Alert Bot ([services/payment_monitor.py](../services/payment_monitor.py))

**Configuration:**
```python
# MIDs to EXCLUDE from alerts and monitoring (test/dummy MIDs)
EXCLUDED_MIDS = [
    '43110201461',  # Test MID - should not trigger alerts
]

# MID Names to EXCLUDE from alerts (case-insensitive partial match)
EXCLUDED_MID_NAMES = [
    'timesaver',    # Test MID name
    'test',         # Generic test MIDs
]
```

**Filter Function:**
```python
def should_exclude_mid(mid_id, mid_name):
    """Check if a MID should be excluded from alerts"""
    # Check by MID ID
    if mid_id and mid_id in EXCLUDED_MIDS:
        return True

    # Check by MID name (case-insensitive partial match)
    if mid_name:
        mid_name_lower = mid_name.lower().strip()
        for excluded_name in EXCLUDED_MID_NAMES:
            if excluded_name in mid_name_lower:
                return True

    return False
```

**Applied In:**
- `check_performance_window()` - Regular performance monitoring
- `check_low_volume_failures()` - Low volume failure detection

### 2. Grafana Dashboard Views ([database/views/create_grafana_views.sql](../database/views/create_grafana_views.sql))

**SQL Filters Added:**
```sql
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND mid_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
```

**Views Updated:**

**Timeout Performance Views:**
- `timeout_performance_5min`
- `timeout_performance_15min`
- `timeout_performance_30min`

**MID + Bank Performance Views:**
- `mid_bank_performance_5min`
- `mid_bank_performance_15min`
- `mid_bank_performance_30min`
- `mid_bank_performance_2hour_baseline`

**Bank Performance Views:**
- `bank_performance_5min`
- `bank_performance_15min`
- `bank_performance_30min`
- `bank_performance_1hour`
- `bank_performance_2hour`
- `bank_performance_today`

**Revenue Views:**
- `revenue_by_currency_5min`
- `revenue_by_currency_15min`
- `revenue_by_currency_30min`
- `revenue_by_currency_1hour`
- `revenue_by_currency_today`

## Adding New Excluded MIDs

### For Telegram Alerts:
Edit [services/payment_monitor.py](../services/payment_monitor.py):

```python
EXCLUDED_MIDS = [
    '43110201461',  # Test MID
    '12345678901',  # Add new MID here
]

EXCLUDED_MID_NAMES = [
    'timesaver',
    'test',
    'demo',  # Add new pattern here
]
```

### For Grafana Dashboards:
1. Edit [database/views/create_grafana_views.sql](../database/views/create_grafana_views.sql)
2. Add the MID to the exclusion list:
   ```sql
   AND mid_id NOT IN ('43110201461', 'NEW_MID_HERE')
   ```
3. Run the migration:
   ```bash
   psql -U webhook_user -d payment_transactions < database/migrations/migration_exclude_test_mids.sql
   ```

## Migration

To apply the Grafana view updates to your database:

```bash
# Apply the comprehensive migration (updates ALL views)
psql -U webhook_user -d payment_transactions -f database/migrations/migration_exclude_test_mids_all_views.sql
```

This migration updates:
- 4 MID + Bank Performance views
- 3 Timeout Performance views
- 6 Bank Performance views
- 5 Revenue views

**Total: 18 views updated** with test MID exclusions

## Verification

### Check Alert Bot Exclusions:
Run the monitoring script and look for skip messages:
```bash
python3 services/payment_monitor.py
```

Expected output:
```
⏭️  Skipping excluded MID: Timesaver (43110201461)
```

### Check Grafana View Exclusions:
```sql
-- Should return 0 rows for excluded MIDs
SELECT * FROM timeout_performance_5min WHERE mid_id = '43110201461';

-- Check all excluded MIDs in raw data
SELECT mid_id, mid_name, COUNT(*)
FROM transactions
WHERE mid_id IN ('43110201461')
   OR mid_name ILIKE '%timesaver%'
GROUP BY mid_id, mid_name;
```

## Example: Before vs After

### Before (Alert Message):
```
🔴 CRITICAL ALERT
━━━━━━━━━━━━━━━━━━━━━
⚠️ All Transactions Failing

MID: Timesaver  ← This was triggering false alerts
Bank: DENIZBANK A.S.
...
```

### After:
```
🔍 Checking 5min window...
⏭️  Skipping excluded MID: Timesaver (43110201461)  ← Now filtered out
   Alerts sent: 0
```

## Notes

- **Case Insensitive**: MID name matching is case-insensitive and uses partial matching
- **Multiple Filters**: Both MID ID and MID name filters work independently
- **NULL Handling**: Views properly handle NULL mid_name values
- **Performance**: Filters are applied in WHERE clause for optimal query performance

## Related Files

**Alert Configuration:**
- [services/payment_monitor.py](../services/payment_monitor.py) - Alert bot with exclusion logic

**View Definitions:**
- [database/views/create_grafana_views.sql](../database/views/create_grafana_views.sql) - Timeout performance views
- [database/views/create_monitoring_views.sql](../database/views/create_monitoring_views.sql) - MID + Bank performance views
- [database/views/create_bank_performance_views.sql](../database/views/create_bank_performance_views.sql) - Bank performance views
- [database/views/create_revenue_views.sql](../database/views/create_revenue_views.sql) - Revenue views

**Migrations:**
- [database/migrations/migration_exclude_test_mids_all_views.sql](../database/migrations/migration_exclude_test_mids_all_views.sql) - Comprehensive migration (ALL views)

## Support

If you need to add more test MIDs to the exclusion list, update both:
1. Python configuration in `payment_monitor.py`
2. SQL views in `create_grafana_views.sql` and run the migration
