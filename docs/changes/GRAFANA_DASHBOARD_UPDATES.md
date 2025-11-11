# Grafana Dashboard Updates Applied
**Date:** 2025-10-28 21:56 UTC
**Dashboard:** Payment Gateway Monitoring

---

## ✅ Changes Applied

### Panel Updates

| Panel ID | Old Title | New Title | Change |
|----------|-----------|-----------|--------|
| **2** | Transaction Status | **Total Revenue by Currency** | ✅ Replaced pie chart with revenue table |
| **6** | Merchant Performance | Merchant Performance | ✅ Added merchant_name column |
| **8** | Success Rate Trends by MID+Bank | **Success Rate Trends by Bank** | ✅ Changed from MID+Bank to Bank only |

---

## 📊 Panel 2: Total Revenue by Currency

**Previous:** Pie chart showing transaction status breakdown (success/declined/pending)

**Now:** Table showing revenue by currency

### New Query:
```sql
SELECT
    currency,
    transaction_count,
    ROUND(total_revenue, 2) as total_revenue,
    ROUND(avg_transaction_amount, 2) as avg_amount
FROM revenue_by_currency_today
ORDER BY total_revenue DESC
```

### What You'll See:
| Currency | Transactions | Total Revenue | Avg Amount |
|----------|--------------|---------------|------------|
| TRY | 3,029 | ₺4,569,459.00 | ₺1,508.57 |
| EUR | 4,809 | €155,562.00 | €32.35 |
| JPY | 3 | ¥51,000.00 | ¥17,000.00 |
| USD | 3 | $104.00 | $34.67 |

---

## 🏪 Panel 6: Merchant Performance

**Previous:** Table showing merchant_id, transactions, success rate

**Now:** Table showing merchant_id, **merchant_name**, transactions, success rate

### New Query:
```sql
SELECT
    merchant_id,
    merchant_name,
    total_transactions,
    successful,
    declined,
    pending,
    success_rate,
    decline_rate
FROM merchant_performance_30min
ORDER BY total_transactions DESC
```

### What Changed:
- ✅ Added `merchant_name` column
- ✅ Shows human-readable merchant names
- ✅ No more duplicate merchant IDs with different names
- ✅ Uses merchant_performance_30min view

---

## 📈 Panel 8: Success Rate Trends by Bank

**Previous:** Time series showing success rates for each MID+Bank combination

**Now:** Time series showing success rates for each Bank (all MIDs aggregated)

### New Query:
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

### What Changed:
- ✅ Simplified from MID+Bank to Bank only
- ✅ Shows overall bank performance across all terminals
- ✅ Cleaner graph with fewer lines
- ✅ Uses bank_performance_5min view
- ✅ Only shows banks with 5+ transactions

---

## 🔧 Database Views Being Used

### Revenue Views:
- `revenue_by_currency_today` - Today's revenue by currency
- `revenue_by_currency_30min` - Last 30 minutes revenue
- `revenue_by_currency_1hour` - Last 1 hour revenue

### Merchant Views:
- `merchant_performance_30min` - Last 30 minutes merchant stats with names
- `merchant_performance_15min` - Last 15 minutes merchant stats
- `merchant_performance_5min` - Last 5 minutes merchant stats

### Bank Views:
- `bank_performance_5min` - Last 5 minutes bank stats
- `bank_performance_30min` - Last 30 minutes bank stats
- `bank_performance_today` - Today's bank stats

---

## 📁 Files Modified

- **Backup:** `/var/lib/grafana/dashboards/payment_monitoring_v2.json.backup_YYYYMMDD_HHMMSS`
- **Updated:** `/var/lib/grafana/dashboards/payment_monitoring_v2.json`
- **Grafana:** Restarted successfully

---

## 🎯 What to Expect

When you refresh your Grafana dashboard, you should now see:

1. **Total Revenue by Currency** (where Transaction Status was)
   - Shows actual revenue amounts in TRY, EUR, JPY, USD
   - Includes transaction counts and average amounts
   - Only counts successful transactions

2. **Merchant Performance** (improved)
   - Now shows merchant names alongside IDs
   - Example: "1995553 - Paytic [LIVE]" instead of just "1995553"
   - Consistent naming across all rows

3. **Success Rate Trends by Bank** (simplified)
   - Shows bank names only: "AKBANK T.A.S.", "DENIZBANK A.S.", etc.
   - No longer shows individual terminals
   - Cleaner, easier to read graph

---

## 🔄 How to View Changes

1. **Open Grafana** at your Grafana URL
2. **Navigate to** "Payment Gateway Monitoring" dashboard
3. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)
4. **Check the updated panels**

If you don't see changes immediately:
- Click the **Refresh** icon in Grafana (top right)
- Set time range to "Last 30 minutes" or "Today"
- Clear browser cache if needed

---

## 📊 Alternative Panel Options (Optional)

### For Revenue Panel (Panel 2):

If you prefer stat boxes instead of a table, you can update Panel 2 to:

**Option A: 4 Separate Stat Boxes**
- Create 4 panels (TRY, EUR, JPY, USD)
- Each with its own query filtering by currency
- See `/opt/payment-webhook/REVENUE_DASHBOARD_GUIDE.md` for details

**Option B: Keep Current Table**
- Already applied ✅
- Shows all currencies in one table

---

## 🐛 Troubleshooting

### If panels show "No Data":
1. Check time range is set to "Last 30 minutes" or "Today"
2. Verify database views exist:
   ```sql
   SELECT * FROM revenue_by_currency_today LIMIT 1;
   SELECT * FROM merchant_performance_30min LIMIT 1;
   SELECT * FROM bank_performance_5min LIMIT 1;
   ```
3. Check Grafana logs: `tail -f /var/log/grafana/grafana.log`

### If queries fail:
1. Verify PostgreSQL connection in Grafana
2. Check webhook_user has SELECT permissions on new views
3. Test queries directly in PostgreSQL

### If changes don't appear:
1. Force refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Restart Grafana: `systemctl restart grafana-server`
4. Check dashboard provisioning: `/etc/grafana/provisioning/dashboards/`

---

## 📝 Next Steps (Optional)

### Additional Customizations:

1. **Add more revenue panels** for different time windows
2. **Create alerts** based on revenue thresholds
3. **Add revenue trend graphs** over time
4. **Create bank comparison panels**
5. **Add currency conversion** if needed

See documentation files for more options:
- `/opt/payment-webhook/REVENUE_DASHBOARD_GUIDE.md`
- `/opt/payment-webhook/BANK_PERFORMANCE_VIEWS.md`
- `/opt/payment-webhook/GRAFANA_FIXES_SUMMARY.md`

---

## ✅ Verification Checklist

- [x] Database views created (revenue, bank, merchant)
- [x] Dashboard backup created
- [x] Dashboard updated with new queries
- [x] Panel 2: Changed to revenue table
- [x] Panel 6: Added merchant_name
- [x] Panel 8: Changed to bank-only trends
- [x] File ownership set correctly
- [x] Grafana restarted successfully

---

**Dashboard is now updated and ready to use!** 🎉

Access your Grafana dashboard and refresh to see the changes.

---

**Last Updated:** 2025-10-28 21:56 UTC
**Created By:** Claude Code AI Assistant
