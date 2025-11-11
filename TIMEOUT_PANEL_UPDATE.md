# Timeout Panel Update - PolPay Dashboard

**Date:** 2025-10-29 09:06 UTC  
**Panel Updated:** Timeout Performance by MID+Bank → Timeout Performance by Merchant

---

## ✅ Changes Applied

### Panel Update

**Old Panel:**
- **Title:** "Timeout Performance by MID+Bank"
- **Grouping:** mid_id, mid_name, bank_name
- **Description:** Showed timeout rates for each terminal (MID) and bank combination

**New Panel:**
- **Title:** "Timeout Performance by Merchant"
- **Grouping:** merchant_id, merchant_name
- **Description:** Shows timeout rates aggregated by merchant

---

## 📊 New Query

```sql
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate
FROM transactions
WHERE $__timeFilter(last_updated_at)
    AND merchant_id IS NOT NULL
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') > 0
ORDER BY timeout_rate DESC NULLS LAST
LIMIT 20
```

---

## 📈 What You'll See

The panel now displays timeout performance data grouped by merchant:

| Column | Description |
|--------|-------------|
| **merchant_id** | Unique merchant identifier |
| **merchant_name** | Human-readable merchant name |
| **total_transactions** | Total number of transactions |
| **timeout_count** | Number of transactions that timed out |
| **successful** | Number of successful transactions |
| **declined** | Number of declined transactions |
| **timeout_rate** | Percentage of transactions that timed out |
| **success_rate** | Overall success rate percentage |

### Example Data:
```
Merchant ID | Merchant Name          | Total Txns | Timeout Count | Success | Declined | Timeout % | Success %
7786186     | Herogaming USD [LIVE]  |     55     |      15       |    8    |    47    |   27.27   |   14.55
4260447     | Herogaming JPY [LIVE]  |     10     |       1       |    2    |     8    |   10.00   |   20.00
7859677     | Multipay [LIVE]        |   1547     |     128       |   919   |   628    |    8.27   |   59.41
4565530     | Multipay MC TRY [LIVE] |   3161     |     257       |  2155   |  1006    |    8.13   |   68.17
1995553     | Paytic [LIVE]          |   5183     |     384       |  3345   |  1838    |    7.41   |   64.54
```

---

## 🎯 Benefits

### Better Insights:
- ✅ See which merchants have the highest timeout rates
- ✅ Identify merchant-level performance issues
- ✅ Simplified view without terminal-level details
- ✅ Easier to correlate with business metrics

### Cleaner Dashboard:
- ✅ Less clutter (no MID+Bank combinations)
- ✅ Merchant-focused view for business users
- ✅ Still shows all key metrics (timeouts, success, declined)

---

## 🔧 Technical Details

### Files Modified:
- **Dashboard:** `/var/lib/grafana/dashboards/polpay_dashboard.json`
- **Backup:** `/var/lib/grafana/dashboards/polpay_dashboard.json.backup_20251029_090608`

### Changes:
1. Updated SQL query to group by merchant_id and merchant_name
2. Removed mid_id, mid_name, and bank_name columns
3. Changed panel title to "Timeout Performance by Merchant"
4. Kept all other metrics (timeout_count, timeout_rate, success_rate, etc.)

### Verification:
```bash
✓ Query tested successfully in PostgreSQL
✓ Dashboard JSON updated
✓ File ownership corrected
✓ Grafana restarted successfully
✓ No errors or warnings in Grafana logs
✓ Dashboard provisioned: polpay-dashboard
```

---

## 📊 Access Updated Dashboard

**URL:** http://23.88.104.43:3001  
**Dashboard:** PolPay Dashboard  
**Updated Panel:** Timeout Performance by Merchant

---

## 🔄 Rollback (If Needed)

To restore the previous version:
```bash
cp /var/lib/grafana/dashboards/polpay_dashboard.json.backup_20251029_090608 \
   /var/lib/grafana/dashboards/polpay_dashboard.json
systemctl restart grafana-server
```

---

**Panel update completed successfully!** 🎉

The timeout performance data is now displayed at the merchant level, making it easier to identify which merchants are experiencing timeout issues.

---

**Last Updated:** 2025-10-29 09:06 UTC
