# Grafana Dashboard Fixes Summary
**Date:** 2025-10-28
**Status:** ✅ All Issues Resolved

---

## 🔍 Issues Identified

### 1. **Duplicate Merchant Names**
- **Problem:** "[ACQ] Gantenpay LIVE" had 2 different merchant IDs (9611509 and 4316065)
- **Root Cause:** Duplicate entry in merchant_mapping table

### 2. **Inconsistent Merchant Names in Transactions**
- **Problem:** Same merchant_id showing with different merchant_name values
  - Example: merchant_id 4565530 appeared as both "Multipay MC TRY [LIVE]" and "Multipay [LIVE]"
  - Example: merchant_id 7859677 appeared as both "Multipay [LIVE]" and "Multipay MC TRY [LIVE]"
- **Root Cause:** Old transactions stored before merchant name lookup was implemented

### 3. **Missing Merchant Names in Grafana Views**
- **Problem:** Grafana dashboards only showed merchant_id, not merchant_name
- **Root Cause:** Views were grouping by merchant_id only without including merchant_name column

---

## ✅ Fixes Applied

### Fix 1: Remove Duplicate Merchant Mapping
```sql
-- Removed merchant_id 9611509 (0 transactions)
-- Kept merchant_id 4316065 (5 transactions)
DELETE FROM merchant_mapping
WHERE merchant_id = '9611509'
  AND merchant_name = '[ACQ] Gantenpay LIVE';
```
**Result:** ✅ 1 duplicate removed

### Fix 2: Update Transaction Merchant Names
```sql
-- Updated all transactions to use correct names from mapping table
UPDATE transactions t
SET merchant_name = m.merchant_name
FROM merchant_mapping m
WHERE t.merchant_id = m.merchant_id
  AND (t.merchant_name IS NULL OR t.merchant_name != m.merchant_name);
```
**Result:** ✅ 1,716 transactions updated

### Fix 3: Recreate Grafana Views with Merchant Names
**Updated Views:**
- `merchant_performance_5min` - Now includes merchant_name column
- `merchant_performance_15min` - Now includes merchant_name column
- `merchant_performance_30min` - Now includes merchant_name column
- `merchant_timeout_5min` - Newly created with merchant_name
- `merchant_timeout_15min` - Newly created with merchant_name
- `merchant_timeout_30min` - Updated with merchant_name column

**Result:** ✅ All 6 views now include both merchant_id and merchant_name

---

## 📊 Verification Results

### Merchant Performance 30min View
| Merchant ID | Merchant Name           | Transactions | Success Rate | Decline Rate |
|-------------|-------------------------|--------------|--------------|--------------|
| 4565530     | Multipay MC TRY [LIVE]  | 117          | 66.67%       | 33.33%       |
| 1995553     | Paytic [LIVE]           | 96           | 64.58%       | 35.42%       |
| 7859677     | Multipay [LIVE]         | 63           | 50.79%       | 49.21%       |
| 5942461     | Paytic MC TRY [LIVE]    | 62           | 72.58%       | 27.42%       |

### All Views Status
| View Name                    | Merchants Count | Status |
|------------------------------|-----------------|--------|
| merchant_performance_5min    | 4               | ✅     |
| merchant_performance_15min   | 4               | ✅     |
| merchant_performance_30min   | 4               | ✅     |
| merchant_timeout_5min        | 4               | ✅     |
| merchant_timeout_15min       | 4               | ✅     |
| merchant_timeout_30min       | 4               | ✅     |

---

## 🎯 Current State

### Merchant Mapping Table
- **Total Merchants:** 84 unique merchants (after removing 1 duplicate)
- **Consistency:** ✅ No duplicate merchant names
- **All merchant IDs have unique names**

### Transactions Table
- **Total Transactions:** 212,708 transactions
- **Merchant Names:** ✅ All consistent with mapping table
- **Recent Transactions:** ✅ All showing correct merchant names

### Grafana Views
- **Merchant Performance Views:** ✅ All include merchant_id and merchant_name
- **Timeout Views:** ✅ All include merchant_id and merchant_name
- **Data Accuracy:** ✅ All merchants with transactions are visible

---

## 📁 Files Created

1. **`/opt/payment-webhook/fix_merchant_data.sql`**
   - Removes duplicate Gantenpay mapping
   - Updates all transaction merchant names
   - Verification queries

2. **`/opt/payment-webhook/update_grafana_views.sql`**
   - Drops old views
   - Creates new views with merchant_name column
   - Grants permissions
   - Verification queries

3. **`/opt/payment-webhook/GRAFANA_FIXES_SUMMARY.md`** (this file)
   - Complete documentation of all fixes

---

## 🔄 Next Steps

### For Grafana Dashboards:
1. Refresh your Grafana dashboards
2. Update queries to use `merchant_name` column for display
3. Group by both `merchant_id` and `merchant_name` for accuracy

### Ongoing Maintenance:
- Webhook app automatically looks up merchant names from mapping table
- All new transactions will have correct merchant names
- No manual intervention needed going forward

---

## 🎉 Summary

**All issues resolved successfully!**

✅ No more duplicate merchant names
✅ All transactions have consistent merchant names
✅ All Grafana views include merchant names
✅ All merchants with transactions are visible in dashboards

**Affected Transactions:** 1,716 fixed
**Total Transactions Verified:** 212,708
**Execution Time:** ~3 seconds
**Downtime:** None (views recreated seamlessly)

---

**Last Updated:** 2025-10-28 21:00 UTC
**Verified By:** Claude Code AI Assistant
