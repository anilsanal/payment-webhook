# Payment Gateway Performance Monitoring System

## Overview

Real-time monitoring system that tracks MID + Bank performance and sends Telegram alerts when decline rates exceed thresholds.

## 🎯 Features

- **Real-time monitoring** of payment gateway performance
- **Multiple time windows**: 5min, 15min, 30min
- **Granular tracking**: Per MID + Bank combination
- **Telegram alerts** for high decline rates
- **Alert cooldown** to prevent spam (30 minutes)
- **Historical logging** of all alerts

## ⚙️ Configuration

### Alert Thresholds

| Time Window | Min Transactions | Warning Threshold | Critical Threshold |
|-------------|-----------------|-------------------|-------------------|
| 5 minutes   | 5               | 40% decline rate  | 60% decline rate  |
| 15 minutes  | 10              | 40% decline rate  | 60% decline rate  |
| 30 minutes  | 20              | 40% decline rate  | 60% decline rate  |

### Environment Variables

Located in `/opt/payment-webhook/.env`:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
DB_NAME=payment_transactions
DB_USER=webhook_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## 📊 Database Views

### Performance Views

- `mid_bank_performance_5min` - Last 5 minutes
- `mid_bank_performance_15min` - Last 15 minutes
- `mid_bank_performance_30min` - Last 30 minutes
- `mid_bank_performance_2hour_baseline` - 2-hour baseline for comparison

### Alert History

- `alert_history` - Log of all alerts sent
- `recent_alerts_summary` - Summary of alerts in last 24 hours

## 🚀 Usage

### Manual Run

```bash
/opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/payment_monitor.py
```

### Automated (Cron)

Runs every 5 minutes automatically:
```
*/5 * * * * /opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/payment_monitor.py >> /var/log/payment_monitor.log 2>&1
```

### View Logs

```bash
tail -f /var/log/payment_monitor.log
```

## 📈 Monitoring Queries

### Check Current Performance

```sql
-- Last 30 minutes performance
SELECT * FROM mid_bank_performance_30min
WHERE decline_rate >= 40
ORDER BY decline_rate DESC;
```

### View Recent Alerts

```sql
SELECT * FROM alert_history
WHERE alert_time >= NOW() - INTERVAL '24 hours'
ORDER BY alert_time DESC;
```

### Alert Summary by MID

```sql
SELECT
    mid_name,
    bank_name,
    COUNT(*) as alert_count,
    AVG(decline_rate) as avg_decline_rate
FROM alert_history
WHERE alert_time >= NOW() - INTERVAL '24 hours'
GROUP BY mid_name, bank_name
ORDER BY alert_count DESC;
```

## 🔧 Maintenance

### Adjust Thresholds

Edit `/opt/payment-webhook/payment_monitor.py`:

```python
THRESHOLDS = {
    '5min': {
        'min_transactions': 5,
        'critical_decline_rate': 60,
        'warning_decline_rate': 40
    },
    # ...
}
```

Then restart cron or wait for next run.

### Change Cooldown Period

```python
COOLDOWN_MINUTES = 30  # Change to desired minutes
```

### Test Telegram Bot

```bash
/opt/payment-webhook/venv/bin/python3 /opt/payment-webhook/test_telegram.py
```

## 📱 Telegram Alert Format

```
🟡 WARNING
━━━━━━━━━━━━━━━━━━━━━
High Decline Rate Detected

MID: SendsCo - LIVE - TRY MC 4
Bank: DENIZBANK A.S.
Window: Last 5min
━━━━━━━━━━━━━━━━━━━━━
📊 Performance:
   ✅ Success: 3 (60.0%)
   ❌ Declined: 2 (40.0%)
   ⏳ Pending: 0
   📈 Total: 5
━━━━━━━━━━━━━━━━━━━━━
⚠️ Threshold: 40% decline rate
📉 Current: 40.0% decline rate
🕒 2025-10-28 11:18:04 UTC
```

## 🐛 Troubleshooting

### Alerts Not Sending

1. Check Telegram bot token and channel ID in `.env`
2. Verify bot is admin in the Telegram group
3. Test manually: `python3 test_telegram.py`
4. Check logs: `tail -f /var/log/payment_monitor.log`

### No Alerts Despite High Decline Rates

- Check if minimum transaction thresholds are met
- Verify cooldown period hasn't blocked alerts
- Check alert_history table for recent alerts

### Database Connection Issues

- Verify database credentials in `.env`
- Test connection: `psql -U webhook_user -d payment_transactions -h localhost`

## 📋 Files

- `/opt/payment-webhook/payment_monitor.py` - Main monitoring script
- `/opt/payment-webhook/test_telegram.py` - Telegram bot tester
- `/opt/payment-webhook/.env` - Configuration
- `/opt/payment-webhook/create_monitoring_views.sql` - Database setup
- `/var/log/payment_monitor.log` - Monitoring logs

## 📞 Support

For issues or questions, check:
- Alert history in database
- Monitoring logs
- Telegram bot status

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
