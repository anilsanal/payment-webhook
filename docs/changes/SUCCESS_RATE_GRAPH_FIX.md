# Success Rate Trends by Bank - Graph Fix

**Date:** 2025-10-29 09:12 UTC  
**Issue:** Success Rate Trends by Bank panel was not displaying graphs  
**Status:** ✅ Fixed

---

## 🔍 **Problem Identified**

### Root Cause:
The panel was using the `bank_performance_5min` view, which aggregates all transactions from the last 5 minutes into a **single row per bank**. This created only **one data point per bank**, which is insufficient for a time series graph.

### Why It Failed:
- Time series graphs need **multiple data points over time**
- The view only provided one aggregated snapshot
- No historical trend data was available

### Old Query (Not Working):
```sql
SELECT
  DATE_TRUNC('minute', last_transaction) as time,
  bank_name as metric,
  success_rate as value
FROM bank_performance_5min
WHERE $__timeFilter(last_transaction)
  AND total_transactions >= 5
ORDER BY time, bank_name
```

**Result:** Only 1-2 data points per bank → No graph visualization

---

## ✅ **Solution Applied**

### New Query (Working):
```sql
SELECT
  DATE_TRUNC('minute', last_updated_at) as time,
  bank_name as metric,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as value
FROM transactions
WHERE $__timeFilter(last_updated_at)
  AND bank_name IS NOT NULL
GROUP BY DATE_TRUNC('minute', last_updated_at), bank_name
HAVING COUNT(*) >= 3
ORDER BY time, bank_name
```

### Key Changes:
1. ✅ **Direct query on `transactions` table** instead of using a view
2. ✅ **Groups by minute buckets** to create multiple time points
3. ✅ **Calculates success rate on-the-fly** for each time bucket
4. ✅ **Minimum 3 transactions per bucket** (reduced from 5 for better coverage)
5. ✅ **Uses `last_updated_at`** for proper time filtering

---

## 📊 **What You'll See Now**

### Graph Display:
- **Multiple lines** - One line per bank showing success rate over time
- **Historical trends** - See how success rates change minute by minute
- **Real-time updates** - Auto-refreshes every 30 seconds
- **Interactive** - Hover to see exact values, zoom in/out

### Example Time Series Data:
```
Time                 | Bank                          | Success Rate
---------------------+-------------------------------+--------------
2025-10-29 07:26:00  | AKBANK T.A.S.                 | 33.33%
2025-10-29 07:28:00  | YAPI VE KREDI BANKASI A.S.    | 100.00%
2025-10-29 07:29:00  | TURKIYE GARANTI BANKASI A.S.  | 66.67%
2025-10-29 07:31:00  | AKBANK T.A.S.                 | 100.00%
2025-10-29 07:32:00  | YAPI VE KREDI BANKASI A.S.    | 33.33%
...and so on
```

---

## 🎯 **Benefits**

### Improved Visibility:
- ✅ **See trends over time** - Identify patterns and anomalies
- ✅ **Compare banks** - Multiple lines on same graph
- ✅ **Real-time monitoring** - Track success rates as they happen
- ✅ **Historical context** - View data from the entire time range

### Better Performance Analysis:
- ✅ Spot sudden drops in success rates
- ✅ Identify which banks are consistently performing well/poorly
- ✅ Correlate events with time-based patterns
- ✅ Make data-driven decisions about routing

---

## 🔧 **Technical Details**

### Query Performance:
- **Before:** Fast (view-based, pre-aggregated)
- **After:** Slightly slower but acceptable (direct table query with grouping)
- **Optimization:** Minimum 3 transactions per bucket reduces noise

### Time Granularity:
- **Bucket Size:** 1 minute
- **Filter:** Shows data for selected time range (default: Last 6 hours, Last 24 hours, etc.)
- **Minimum Transactions:** 3 per minute per bank (filters out sparse data)

### Files Modified:
- **Dashboard:** `/var/lib/grafana/dashboards/polpay_dashboard.json`
- **Backup:** `/var/lib/grafana/dashboards/polpay_dashboard.json.backup_timeseries`

---

## 🧪 **Testing Results**

### Query Test (Last 2 Hours):
```bash
✓ Returns 20+ data points across multiple banks
✓ Each bank has multiple time entries
✓ Success rates calculated correctly
✓ Time series format validated
```

### Grafana Verification:
```bash
✓ Dashboard JSON updated successfully
✓ Grafana restarted without errors
✓ No warnings in logs
✓ Panel configured as timeseries type
```

---

## 📊 **Access Updated Dashboard**

**URL:** http://23.88.104.43:3001  
**Dashboard:** PolPay Dashboard  
**Fixed Panel:** Success Rate Trends by Bank

### How to View:
1. Open the dashboard
2. Locate the "Success Rate Trends by Bank" panel
3. You should now see line graphs showing success rates over time
4. Use the time range selector to adjust the view (Last 6h, Last 24h, etc.)

---

## 🔄 **Rollback (If Needed)**

To restore the previous version:
```bash
cp /var/lib/grafana/dashboards/polpay_dashboard.json.backup_timeseries \
   /var/lib/grafana/dashboards/polpay_dashboard.json
systemctl restart grafana-server
```

---

## 💡 **Tips for Best Results**

### Recommended Time Ranges:
- **Last 6 hours** - Good for recent trends
- **Last 24 hours** - See daily patterns
- **Last 7 days** - Long-term performance analysis

### Graph Settings:
- **Auto-refresh:** 30 seconds (already configured)
- **Legend:** Shows all banks with color coding
- **Tooltip:** Hover over lines to see exact values

---

## 🎉 **Result**

The Success Rate Trends by Bank graph now displays properly with multiple data points over time, allowing you to:
- ✅ Monitor bank performance trends
- ✅ Identify problematic periods
- ✅ Compare banks side-by-side
- ✅ Make informed routing decisions

---

**Fix completed successfully!** 🎉

The graph should now display time series lines showing how each bank's success rate changes over time.

---

**Last Updated:** 2025-10-29 09:12 UTC  
**Issue:** Resolved ✅
