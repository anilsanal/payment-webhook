# Revenue Dashboard Guide for Grafana
**Created:** 2025-10-28
**Purpose:** Replace Transaction Status with Total Revenue by Currency

---

## 📊 Available Revenue Views

| View Name | Time Window | Description |
|-----------|-------------|-------------|
| `revenue_by_currency_5min` | Last 5 minutes | Real-time revenue |
| `revenue_by_currency_15min` | Last 15 minutes | Short-term revenue |
| `revenue_by_currency_30min` | Last 30 minutes | Medium-term revenue |
| `revenue_by_currency_1hour` | Last 1 hour | Hourly revenue |
| `revenue_by_currency_today` | Today (00:00 - now) | Daily revenue |
| `revenue_summary_all_windows` | Multiple windows | Comparison view |

---

## 💰 Current Revenue (Today)

| Currency | Transactions | Total Revenue | Avg Amount |
|----------|--------------|---------------|------------|
| **TRY** | 3,029 | ₺4,569,459.00 | ₺1,508.57 |
| **EUR** | 4,809 | €155,562.00 | €32.35 |
| **JPY** | 3 | ¥51,000.00 | ¥17,000.00 |
| **USD** | 3 | $104.00 | $34.67 |

---

## 📈 View Structure

Each view contains:

| Column | Type | Description |
|--------|------|-------------|
| `currency` | VARCHAR | Currency code (TRY, EUR, JPY, USD) |
| `transaction_count` | INTEGER | Number of successful transactions |
| `total_revenue` | DECIMAL | Sum of all successful transaction amounts |
| `avg_transaction_amount` | DECIMAL | Average transaction amount |
| `min_amount` | DECIMAL | Smallest transaction amount |
| `max_amount` | DECIMAL | Largest transaction amount |
| `first_transaction` | TIMESTAMP | Time of first transaction |
| `last_transaction` | TIMESTAMP | Time of last transaction |

**Important:** Only **successful** transactions are counted!

---

## 🎨 Grafana Panel Configurations

### Option 1: Stat Boxes (Recommended for Dashboard)

Create 4 separate stat panels, one for each currency:

#### Panel: TRY Revenue (Today)
```sql
SELECT
    total_revenue as "Total Revenue",
    transaction_count as "Transactions"
FROM revenue_by_currency_today
WHERE currency = 'TRY';
```

**Visualization Settings:**
- Type: **Stat**
- Title: **Total Revenue (TRY)**
- Value: `total_revenue`
- Unit: Custom (₺)
- Decimal: 2
- Color: Blue
- Show: Both value and name

#### Panel: EUR Revenue (Today)
```sql
SELECT
    total_revenue as "Total Revenue",
    transaction_count as "Transactions"
FROM revenue_by_currency_today
WHERE currency = 'EUR';
```

**Visualization Settings:**
- Type: **Stat**
- Title: **Total Revenue (EUR)**
- Value: `total_revenue`
- Unit: Currency (€)
- Decimal: 2
- Color: Green
- Show: Both value and name

#### Panel: JPY Revenue (Today)
```sql
SELECT
    total_revenue as "Total Revenue",
    transaction_count as "Transactions"
FROM revenue_by_currency_today
WHERE currency = 'JPY';
```

#### Panel: USD Revenue (Today)
```sql
SELECT
    total_revenue as "Total Revenue",
    transaction_count as "Transactions"
FROM revenue_by_currency_today
WHERE currency = 'USD';
```

---

### Option 2: Combined Table

Show all currencies in one table:

```sql
SELECT
    currency,
    transaction_count,
    ROUND(total_revenue, 2) as total_revenue,
    ROUND(avg_transaction_amount, 2) as avg_amount
FROM revenue_by_currency_today
ORDER BY total_revenue DESC;
```

**Visualization Settings:**
- Type: **Table**
- Title: **Revenue by Currency (Today)**
- Columns: All visible
- Sort: By total_revenue DESC

---

### Option 3: Bar Chart

Show revenue comparison across currencies:

```sql
SELECT
    currency,
    total_revenue,
    transaction_count
FROM revenue_by_currency_today
ORDER BY total_revenue DESC;
```

**Visualization Settings:**
- Type: **Bar chart**
- X-axis: currency
- Y-axis: total_revenue
- Legend: Show transaction count
- Orientation: Vertical

---

### Option 4: Time-based Comparison

Compare revenue across different time windows:

```sql
SELECT
    time_window,
    currency,
    total_revenue,
    transaction_count
FROM revenue_summary_all_windows
ORDER BY
    CASE time_window
        WHEN '30 Min' THEN 1
        WHEN '1 Hour' THEN 2
        WHEN 'Today' THEN 3
    END,
    total_revenue DESC;
```

**Visualization Settings:**
- Type: **Grouped bar chart**
- Group by: time_window
- Series: currency
- Value: total_revenue

---

## 🎯 Recommended Dashboard Layout

### Layout 1: Stat Boxes (Like Transaction Status)

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ TRY Revenue  │ EUR Revenue  │ JPY Revenue  │ USD Revenue  │
│ ₺4,569,459   │ €155,562     │ ¥51,000      │ $104         │
│ 3,029 trans  │ 4,809 trans  │ 3 trans      │ 3 trans      │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Panel Configuration:**
- Width: 6 units each (4 panels = 24 units total)
- Height: 4-5 units
- Refresh: 1 minute
- Query: Use Option 1 above (separate query per currency)

---

### Layout 2: Combined View

```
┌─────────────────────────────────────────────────────────┐
│ Total Revenue (Today)                                   │
│ ┌─────────────────────────────────────────────────────┐│
│ │ TRY: ₺4,569,459 (3,029 trans) │ 62%                ││
│ │ EUR: €155,562   (4,809 trans) │ 35%                ││
│ │ JPY: ¥51,000    (3 trans)     │ 2%                 ││
│ │ USD: $104       (3 trans)     │ 1%                 ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Advanced Queries

### Query 1: Revenue Trend (Last Hour)
```sql
SELECT
    DATE_TRUNC('minute', last_transaction) as time,
    currency,
    total_revenue
FROM revenue_by_currency_5min
WHERE last_transaction >= NOW() - INTERVAL '1 hour'
ORDER BY time;
```

### Query 2: Revenue Growth (30min vs 1hour)
```sql
SELECT
    r30.currency,
    r30.total_revenue as revenue_30min,
    r1h.total_revenue as revenue_1hour,
    ROUND(((r30.total_revenue / NULLIF(r1h.total_revenue, 0)) * 100), 2) as percentage_of_hour
FROM revenue_by_currency_30min r30
LEFT JOIN revenue_by_currency_1hour r1h ON r30.currency = r1h.currency
ORDER BY r30.total_revenue DESC;
```

### Query 3: Revenue Per Transaction
```sql
SELECT
    currency,
    total_revenue,
    transaction_count,
    ROUND(total_revenue / NULLIF(transaction_count, 0), 2) as revenue_per_transaction
FROM revenue_by_currency_today
ORDER BY revenue_per_transaction DESC;
```

---

## 🎨 Color Schemes

### Currency Colors (Recommended)
- **TRY**: Blue (`#3f8cff`)
- **EUR**: Green (`#00ff7f`)
- **JPY**: Orange (`#ff9800`)
- **USD**: Purple (`#9c27b0`)

### Threshold Colors
- **High Revenue**: Green (>100,000)
- **Medium Revenue**: Yellow (10,000-100,000)
- **Low Revenue**: Red (<10,000)

---

## 🔄 Grafana Variables (Optional)

Create a dashboard variable for time window selection:

**Variable Name:** `time_window`

**Type:** Custom

**Values:**
```
5min : revenue_by_currency_5min
15min : revenue_by_currency_15min
30min : revenue_by_currency_30min
1hour : revenue_by_currency_1hour
today : revenue_by_currency_today
```

**Query with Variable:**
```sql
SELECT
    currency,
    total_revenue,
    transaction_count
FROM ${time_window}
ORDER BY total_revenue DESC;
```

---

## 📊 Example Stat Panel JSON

```json
{
  "datasource": "PostgreSQL",
  "targets": [
    {
      "rawSql": "SELECT total_revenue, transaction_count FROM revenue_by_currency_today WHERE currency = 'TRY'",
      "format": "table"
    }
  ],
  "type": "stat",
  "title": "Total Revenue (TRY)",
  "options": {
    "reduceOptions": {
      "values": false,
      "fields": "/^total_revenue$/",
      "calcs": ["lastNotNull"]
    },
    "orientation": "auto",
    "textMode": "value_and_name",
    "colorMode": "value",
    "graphMode": "none"
  },
  "fieldConfig": {
    "defaults": {
      "unit": "currencyTRY",
      "decimals": 2,
      "color": {
        "mode": "thresholds"
      },
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"value": 0, "color": "red"},
          {"value": 100000, "color": "yellow"},
          {"value": 1000000, "color": "green"}
        ]
      }
    }
  }
}
```

---

## 🧪 Testing Queries

Run these to verify views are working:

```sql
-- Test 1: Check all views have data
SELECT
    'revenue_by_currency_today' as view_name,
    COUNT(*) as currency_count,
    SUM(total_revenue) as total_revenue_all
FROM revenue_by_currency_today;

-- Test 2: Verify only successful transactions counted
SELECT
    status,
    COUNT(*) as count
FROM transactions
WHERE DATE(last_updated_at) = CURRENT_DATE
  AND trans_amount IS NOT NULL
GROUP BY status;

-- Test 3: Compare with raw data
SELECT
    trans_currency,
    SUM(trans_amount) as raw_sum,
    (SELECT total_revenue FROM revenue_by_currency_today WHERE currency = trans_currency) as view_sum
FROM transactions
WHERE DATE(last_updated_at) = CURRENT_DATE
  AND status = 'success'
  AND trans_amount IS NOT NULL
GROUP BY trans_currency;
```

---

## 📱 Mobile Responsive Layout

For mobile dashboards, stack vertically:

```
┌─────────────────────┐
│ TRY Revenue         │
│ ₺4,569,459          │
│ 3,029 transactions  │
├─────────────────────┤
│ EUR Revenue         │
│ €155,562            │
│ 4,809 transactions  │
├─────────────────────┤
│ JPY Revenue         │
│ ¥51,000             │
│ 3 transactions      │
├─────────────────────┤
│ USD Revenue         │
│ $104                │
│ 3 transactions      │
└─────────────────────┘
```

---

## ⚡ Performance Tips

1. **Use appropriate time windows** - Don't query `revenue_by_currency_today` if you only need 30min data
2. **Set refresh interval** - 1 minute for real-time, 5 minutes for daily views
3. **Use caching** - Enable query result caching in Grafana
4. **Index is already present** - Views use `last_updated_at` which is indexed

---

## 🔐 Permissions

All views are accessible by:
- ✅ `webhook_user` - SELECT permission granted
- ✅ `postgres` - Full access
- ✅ Grafana/Metabase connections

---

## 📝 Quick Setup Steps

1. **Create 4 Stat Panels** in Grafana dashboard
2. **Use queries from Option 1** (one per currency)
3. **Set panel width** to 6 units each
4. **Configure colors** using currency color scheme
5. **Set refresh** to 1 minute
6. **Position** where "Transaction Status" was

**Done!** 🎉

---

**Last Updated:** 2025-10-28 21:50 UTC
**Created By:** Claude Code AI Assistant
