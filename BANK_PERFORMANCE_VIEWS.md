# Bank Performance Views for Grafana
**Created:** 2025-10-28
**Purpose:** Success rate trends by bank only (all MIDs aggregated)

---

## 📊 Available Views

### Time-based Views

| View Name | Time Window | Description |
|-----------|-------------|-------------|
| `bank_performance_5min` | Last 5 minutes | Real-time bank performance |
| `bank_performance_15min` | Last 15 minutes | Short-term trends |
| `bank_performance_30min` | Last 30 minutes | Medium-term trends |
| `bank_performance_1hour` | Last 1 hour | Hourly performance |
| `bank_performance_2hour` | Last 2 hours | Baseline for comparison |
| `bank_performance_today` | Today (00:00 - now) | Daily aggregation |

---

## 📈 View Structure

Each view contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `bank_name` | VARCHAR | Bank name (e.g., "AKBANK T.A.S.") |
| `total_transactions` | INTEGER | Total transaction count |
| `successful` | INTEGER | Successful transaction count |
| `declined` | INTEGER | Declined transaction count |
| `pending` | INTEGER | Pending transaction count |
| `success_rate` | DECIMAL | Success rate percentage (0-100) |
| `decline_rate` | DECIMAL | Decline rate percentage (0-100) |
| `first_transaction` | TIMESTAMP | Time of first transaction in window |
| `last_transaction` | TIMESTAMP | Time of last transaction in window |

---

## 🎨 Grafana Configuration

### For "Success Rate Trends by Bank" Graph

**Query Example:**
```sql
SELECT
    bank_name,
    success_rate,
    decline_rate,
    total_transactions
FROM bank_performance_30min
ORDER BY total_transactions DESC;
```

**Recommended Visualization:**
- **Type:** Time series or Bar gauge
- **X-axis:** bank_name
- **Y-axis:** success_rate
- **Color:** Success rate (green > 80%, yellow 60-80%, red < 60%)

### Time Series Query (for trends over time)
```sql
SELECT
    $__timeGroup(last_transaction, '5m') as time,
    bank_name,
    AVG(success_rate) as success_rate
FROM bank_performance_5min
WHERE $__timeFilter(last_transaction)
GROUP BY time, bank_name
ORDER BY time;
```

---

## 📊 Current Bank Performance (30 min window)

| Bank Name | Transactions | Success Rate | Decline Rate |
|-----------|-------------|--------------|--------------|
| AKBANK T.A.S. | 130 | 79.23% | 20.77% |
| DENIZBANK A.S. | 91 | 80.22% | 19.78% |
| YAPI VE KREDI BANKASI A.S. | 90 | 88.89% | 11.11% |
| TURKIYE GARANTI BANKASI A.S. | 46 | 63.04% | 36.96% |
| TURKIYE HALK BANKASI A.S. | 28 | 92.86% | 7.14% |

---

## 🔄 Key Differences from MID+Bank Views

### Old Views (MID+Bank):
- `mid_bank_performance_5min`
- `mid_bank_performance_15min`
- `mid_bank_performance_30min`
- Grouped by: `mid_id`, `mid_name`, `bank_name`
- **Use case:** Detailed analysis per terminal and bank combination

### New Views (Bank Only):
- `bank_performance_5min`
- `bank_performance_15min`
- `bank_performance_30min`
- Grouped by: `bank_name` only
- **Use case:** Overall bank performance trends across all terminals

---

## 🎯 Use Cases

### 1. Bank Health Dashboard
Monitor overall bank performance without MID complexity:
```sql
SELECT
    bank_name,
    total_transactions,
    success_rate,
    CASE
        WHEN success_rate >= 80 THEN 'Healthy'
        WHEN success_rate >= 60 THEN 'Warning'
        ELSE 'Critical'
    END as health_status
FROM bank_performance_30min
ORDER BY total_transactions DESC;
```

### 2. Success Rate Comparison
Compare success rates across different time windows:
```sql
SELECT
    b30.bank_name,
    b30.success_rate as rate_30min,
    b1h.success_rate as rate_1hour,
    b2h.success_rate as rate_2hour,
    (b30.success_rate - b2h.success_rate) as trend
FROM bank_performance_30min b30
JOIN bank_performance_1hour b1h ON b30.bank_name = b1h.bank_name
JOIN bank_performance_2hour b2h ON b30.bank_name = b2h.bank_name
ORDER BY trend DESC;
```

### 3. Top/Bottom Performers
```sql
-- Top 5 performing banks
SELECT bank_name, success_rate, total_transactions
FROM bank_performance_30min
WHERE total_transactions >= 10
ORDER BY success_rate DESC
LIMIT 5;

-- Bottom 5 performing banks
SELECT bank_name, success_rate, total_transactions
FROM bank_performance_30min
WHERE total_transactions >= 10
ORDER BY success_rate ASC
LIMIT 5;
```

---

## 🔧 Grafana Panel Examples

### Panel 1: Success Rate by Bank (Bar Chart)
```
Data Source: PostgreSQL
Query: SELECT bank_name, success_rate FROM bank_performance_30min ORDER BY success_rate DESC;
Visualization: Bar chart (horizontal)
Legend: Show success rate values
Thresholds: Green (>80%), Yellow (60-80%), Red (<60%)
```

### Panel 2: Bank Transaction Volume (Stat)
```
Data Source: PostgreSQL
Query: SELECT SUM(total_transactions) FROM bank_performance_30min;
Visualization: Stat
Title: Total Transactions (30 min)
```

### Panel 3: Success Rate Trends (Time Series)
```
Data Source: PostgreSQL
Query: Use time series query from above
Visualization: Time series
Y-axis: Success rate (%)
Legend: Show bank names
Refresh: 1 minute
```

---

## ⚡ Performance Notes

- All views are indexed on `last_updated_at`
- Views are calculated on-demand (no caching)
- Minimum 1 transaction required to appear in results
- NULL bank_name values are excluded
- Views auto-refresh when queried

---

## 🔐 Permissions

All views are accessible by:
- ✅ `webhook_user` - SELECT permission granted
- ✅ `postgres` - Full access
- ✅ Metabase/Grafana connections using webhook_user credentials

---

## 📝 Example Grafana Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ Success Rate Trends by Bank (Last 30 minutes)          │
│ [Time Series Graph showing all banks]                  │
├─────────────────────────────────────────────────────────┤
│ Top Performers        │ Bottom Performers               │
│ [Table: Top 5 banks] │ [Table: Bottom 5 banks]        │
├─────────────────────────────────────────────────────────┤
│ Bank Health Status                                      │
│ [Bar gauge showing all banks colored by health]        │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Testing Queries

Run these queries to verify views are working:

```sql
-- Test 1: Check view exists
SELECT COUNT(*) FROM bank_performance_30min;

-- Test 2: Check data quality
SELECT
    COUNT(DISTINCT bank_name) as total_banks,
    SUM(total_transactions) as total_trans,
    ROUND(AVG(success_rate), 2) as avg_success_rate
FROM bank_performance_30min;

-- Test 3: Check time filtering
SELECT
    MIN(first_transaction) as oldest,
    MAX(last_transaction) as newest,
    EXTRACT(EPOCH FROM (MAX(last_transaction) - MIN(first_transaction)))/60 as window_minutes
FROM bank_performance_30min;
```

---

**Last Updated:** 2025-10-28 21:40 UTC
**Created By:** Claude Code AI Assistant
