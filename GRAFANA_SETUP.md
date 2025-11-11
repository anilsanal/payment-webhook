# Grafana Payment Monitoring Dashboard

## 🎯 Overview

Grafana is now installed and configured with a comprehensive real-time payment monitoring dashboard. The system tracks MID+Bank performance, merchant success rates, and timeout rates with automatic 30-second refresh.

---

## 🌐 Access Information

### **Dashboard URL**
```
http://23.88.104.43:3001
```

**Note:** Port 3001 is used because Metabase is already using port 3000.

### **Login Credentials**
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **Important:** Change the password after first login for security!

---

## 📊 Dashboard Features

### **Overview Panels (Top Row)**
1. **Success Rate (30min)** - Overall success rate with color coding
   - 🟢 Green: >90%
   - 🟡 Yellow: 60-90%
   - 🔴 Red: <60%

2. **Transaction Status Pie Chart** - Visual breakdown of success/declined/pending

3. **Timeout Rate (30min)** - Percentage of timeout transactions

4. **Total Transactions (30min)** - Volume counter

### **Main Performance Tables**

#### **MID + Bank Performance**
- Shows top 20 MID+Bank combinations by decline rate
- Color-coded success and decline rates
- Auto-sorted by worst performing first
- Columns: MID ID, MID Name, Bank, Total TXN, Success Count, Declined, Pending, Success %, Decline %

#### **Merchant Performance**
- All merchants with transaction counts
- Success/decline rates per merchant
- Sorted by transaction volume
- Tracks merchant_id performance

#### **Timeout Performance**
- MID+Bank combinations with timeout issues
- Shows timeout count and timeout rate %
- Filtered to show only combinations with timeouts
- Color-coded:
  - 🟢 Green: <10%
  - 🟡 Yellow: 10-20%
  - 🔴 Red: >20%

### **Trend Visualization**
- **Success Rate Trends** - Time series graph showing performance over last 2 hours
- Multiple lines for different MID+Bank combinations
- Interactive hover for details

### **Alert History**
- Last 24 hours of Telegram alerts
- Shows severity, time window, MID+Bank, decline rate
- Limited to 50 most recent alerts

---

## ⚙️ Configuration

### **Auto-Refresh**
- **Current Setting:** 30 seconds
- **How to Change:** Click refresh dropdown in top-right corner
- **Options:** 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h

### **Time Range**
- **Default:** Last 30 minutes
- **How to Change:** Click time range picker in top-right
- **Quick Ranges:** 5m, 15m, 30m, 1h, 6h, 24h, 7d, 30d

### **Timezone**
- **Current:** UTC
- **How to Change:** User Profile → Preferences → Timezone

---

## 🗄️ Database Views

The following PostgreSQL views were created for the dashboard:

### **MID+Bank Performance Views**
- `mid_bank_performance_5min`
- `mid_bank_performance_15min`
- `mid_bank_performance_30min`

### **Merchant Performance Views**
- `merchant_performance_5min`
- `merchant_performance_15min`
- `merchant_performance_30min`

### **Timeout Tracking Views**
- `timeout_performance_5min`
- `timeout_performance_15min`
- `timeout_performance_30min`
- `merchant_timeout_30min`

---

## 🔧 Grafana Service Management

### **Check Status**
```bash
sudo systemctl status grafana-server
```

### **Start/Stop/Restart**
```bash
sudo systemctl start grafana-server
sudo systemctl stop grafana-server
sudo systemctl restart grafana-server
```

### **View Logs**
```bash
sudo journalctl -u grafana-server -f
```

### **Grafana Logs Location**
```
/var/log/grafana/grafana.log
```

---

## 📁 File Locations

### **Configuration**
- Main config: `/etc/grafana/grafana.ini`
- Datasource: `/etc/grafana/provisioning/datasources/postgresql.yaml`
- Dashboard provisioning: `/etc/grafana/provisioning/dashboards/dashboards.yaml`

### **Dashboards**
- Dashboard JSON: `/var/lib/grafana/dashboards/payment_monitoring.json`
- Database views SQL: `/opt/payment-webhook/create_grafana_views.sql`

### **Data & Plugins**
- Data directory: `/var/lib/grafana/`
- Plugins: `/var/lib/grafana/plugins/`

---

## 🎨 Customization

### **Edit Dashboard**
1. Click dashboard title → Settings (⚙️)
2. Add/remove panels
3. Modify queries
4. Adjust thresholds
5. Save changes

### **Add New Panel**
1. Click "Add" → "Visualization"
2. Select datasource: "PaymentTransactions"
3. Write SQL query
4. Configure visualization type
5. Set thresholds and colors
6. Apply

### **Example Query for Custom Panel**
```sql
SELECT
  DATE_TRUNC('minute', last_updated_at) as time,
  merchant_id as metric,
  COUNT(*) as value
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '1 hour'
GROUP BY time, merchant_id
ORDER BY time
```

---

## 🚨 Threshold Configuration

### **Current Alert Thresholds**

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Success Rate | >90% | 60-90% | <60% |
| Decline Rate | <40% | 40-60% | >60% |
| Timeout Rate | <10% | 10-20% | >20% |

### **Modify Thresholds**
1. Edit panel → Field tab
2. Scroll to "Thresholds"
3. Adjust values
4. Change colors if needed
5. Apply

---

## 🔐 Security Recommendations

### **Change Admin Password**
1. Login with admin/admin123
2. Click profile icon (bottom-left)
3. Preferences → Change Password
4. Use strong password

### **Create Additional Users** (Optional)
1. Configuration (⚙️) → Users
2. New User
3. Set username, email, password
4. Assign role: Viewer (read-only) or Editor

### **Configure Firewall** (Optional)
If you want to restrict access:
```bash
sudo ufw allow from YOUR_IP_ADDRESS to any port 3000
sudo ufw enable
```

---

## 📊 Dashboard Tips

### **Best Practices**
1. **Monitor regularly:** Check dashboard 2-3 times per day
2. **Watch trends:** Look for patterns in success rate graph
3. **Set bookmarks:** Bookmark the dashboard URL for quick access
4. **Use filters:** Click on any value to filter the entire dashboard
5. **Export data:** Click panel title → Inspect → Data → Download CSV

### **Performance Optimization**
- For better performance with large datasets, increase refresh interval
- Use shorter time ranges (15min instead of 24h) for faster queries
- Archive old alert_history data monthly

---

## 🐛 Troubleshooting

### **Dashboard Not Loading**
```bash
# Check Grafana is running
sudo systemctl status grafana-server

# Restart if needed
sudo systemctl restart grafana-server

# Check logs
sudo tail -f /var/log/grafana/grafana.log
```

### **"No Data" in Panels**
- Check database connection: Grafana → Configuration → Data Sources → PaymentTransactions → Test
- Verify transactions exist: `SELECT COUNT(*) FROM transactions WHERE last_updated_at >= NOW() - INTERVAL '30 minutes';`
- Check time range matches data

### **Cannot Login**
- Reset password: `sudo grafana-cli admin reset-admin-password newpassword`
- Check service is running: `sudo systemctl status grafana-server`

### **Slow Dashboard**
- Increase refresh interval (30s → 1m)
- Reduce time range (6h → 1h)
- Add indexes to database if needed

---

## 🔗 Useful Links

- **Grafana Documentation:** https://grafana.com/docs/
- **PostgreSQL Data Source:** https://grafana.com/docs/grafana/latest/datasources/postgres/
- **Dashboard Best Practices:** https://grafana.com/docs/grafana/latest/dashboards/

---

## 📞 Support

For issues with:
- **Grafana itself:** Check logs and documentation
- **Database queries:** Verify views exist in PostgreSQL
- **Data not appearing:** Check webhook receiver is running and processing transactions

---

**Installation Date:** 2025-10-28
**Grafana Version:** 12.2.1
**Dashboard Version:** 1.0
