# Payment Webhook System

Production-ready FastAPI webhook receiver for Coriunder payment gateway with real-time monitoring, alerting, and analytics.

[![Deploy Status](https://github.com/anilsanal/payment-webhook/workflows/Deploy%20to%20Production/badge.svg)](https://github.com/anilsanal/payment-webhook/actions)

## 🎯 Overview

This system receives payment transaction webhooks from the Coriunder payment gateway, stores them in PostgreSQL, and provides:

- ✅ Real-time transaction processing
- 📊 Comprehensive Grafana dashboards
- 🔔 Intelligent Telegram alerts for performance issues
- 📈 Multi-timeframe monitoring (5min, 15min, 30min)
- 🏦 BIN-to-bank name resolution
- 🔍 Merchant and terminal (MID) performance tracking
- 📝 Complete audit trail

## 📁 Project Structure

```
payment-webhook/
├── app/                      # Main application
│   └── webhook_app.py        # FastAPI webhook receiver
│
├── services/                 # Background services
│   ├── payment_monitor.py    # Real-time monitoring (cron job)
│   └── payment_daily_report.py
│
├── utils/                    # Utility scripts
│   ├── bin_import.py         # BIN data import
│   ├── mid_import.py         # MID mapping import
│   └── telegram_setup.py     # Bot configuration
│
├── database/                 # Database files
│   ├── schema/              # Table definitions
│   ├── migrations/          # Schema changes
│   ├── views/               # Grafana SQL views
│   └── seeds/               # Initial data
│
├── data/                     # Static data
│   └── BINS_and_BANKS_List.csv
│
├── scripts/                  # Deployment scripts
│   ├── deploy.sh            # Production deployment
│   ├── auto_deploy.sh       # Local → GitHub → Server
│   └── install.sh           # Initial setup
│
├── tests/                    # Test suite
│   └── (coming soon)
│
└── docs/                     # Documentation
    ├── setup/               # Installation guides
    ├── guides/              # User guides
    └── changes/             # Change logs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Linux server with systemd (for production)

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/anilsanal/payment-webhook.git
cd payment-webhook
```

**2. Set up environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

**4. Initialize database:**
```bash
psql -U postgres -f database/schema/database_schema.sql
```

**5. Run locally:**
```bash
python3 -m uvicorn app.webhook_app:app --reload --port 8000
```

**6. Test:**
```bash
curl http://localhost:8000/health
```

## 🏭 Production Deployment

See [docs/setup/DEPLOYMENT.md](docs/setup/DEPLOYMENT.md) for complete deployment guide.

**Quick deployment:**
```bash
# From local machine
./scripts/auto_deploy.sh
```

This will:
- Push code to GitHub
- Trigger CI/CD pipeline
- Deploy to production server
- Run health checks
- Auto-rollback on failure

## 📊 Monitoring

### Grafana Dashboards

Access: `http://your-server:3001`

**Available dashboards:**
- Real-time Performance (30-second refresh)
- MID + Bank Performance
- Merchant Analytics
- Timeout Analysis
- Revenue Tracking
- Alert History

See [docs/setup/GRAFANA_SETUP.md](docs/setup/GRAFANA_SETUP.md) for configuration.

### Telegram Alerts

The system sends intelligent alerts for:
- High decline rates (>50-75% depending on time window)
- Complete failures (all transactions declining)
- Low-volume issues

Excluded from alerts:
- Insufficient funds declines
- Risk management system declines

Configure: [docs/setup/MONITORING_README.md](docs/setup/MONITORING_README.md)

## 🏗️ Architecture

### Data Flow

```
Payment Gateway
    ↓ (GET/POST webhook)
FastAPI App (webhook_app.py)
    ↓
PostgreSQL
    ├── webhook_events (audit trail)
    └── transactions (latest status)
    ↓
Grafana Views
    ↓
Dashboards + Alerts
```

### Database Tables

- **webhook_events**: Full audit trail (every webhook)
- **transactions**: Latest status per transaction (keyed by trans_order)
- **bin_bank_mapping**: BIN → Bank name lookup (1,103 BINs)
- **merchant_mapping**: Merchant ID → Name (84 merchants)
- **mid_mapping**: Terminal/MID mappings
- **alert_history**: Alert log with cooldown tracking

## 🔧 Configuration

### Environment Variables

Required in `.env`:

```bash
# Database
DB_NAME=payment_transactions
DB_USER=webhook_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHANNEL_ID=-100123456789

# Optional
LOG_LEVEL=INFO
```

### Alert Thresholds

Edit in `services/payment_monitor.py`:

```python
THRESHOLDS = {
    '5min':  {'min_transactions': 8,  'critical': 75%, 'warning': 60%},
    '15min': {'min_transactions': 13, 'critical': 75%, 'warning': 50%},
    '30min': {'min_transactions': 25, 'critical': 70%, 'warning': 50%}
}
```

## 📝 Common Tasks

### Import BIN Data

```bash
cd /opt/payment-webhook
source venv/bin/activate
python3 utils/bin_import.py data/BINS_and_BANKS_List.csv
```

### View Service Logs

```bash
# Real-time application logs
sudo journalctl -u webhook-receiver.service -f

# Or file-based logs
tail -f /var/log/webhook_receiver.log

# Monitor logs
tail -f /var/log/payment_monitor.log
```

### Check Service Status

```bash
sudo systemctl status webhook-receiver
curl http://localhost:8000/health
```

### Manual Deployment

```bash
cd /opt/payment-webhook
git pull origin main
sudo systemctl restart webhook-receiver
```

## 🧪 Testing

```bash
# Run tests (when available)
pytest tests/ -v

# Test webhook endpoint
curl -X POST http://localhost:8000/webhook \
  -d "trans_order=TEST123&reply_code=000&merchant_id=1"

# Test Telegram alerts
python3 utils/test_telegram.py
```

## 📖 Documentation

### Setup Guides
- [Deployment Guide](docs/setup/DEPLOYMENT.md)
- [CI/CD Setup](docs/setup/CI_CD_SETUP_GUIDE.md)
- [Grafana Configuration](docs/setup/GRAFANA_SETUP.md)
- [Monitoring Setup](docs/setup/MONITORING_README.md)

### User Guides
- [Quick Reference](docs/guides/QUICK_REFERENCE.md)
- [Grafana Sharing Guide](docs/guides/GRAFANA_SHARING_GUIDE.md)
- [Revenue Dashboard](docs/guides/REVENUE_DASHBOARD_GUIDE.md)

### Analysis Reports
- [BIN Analysis Report](docs/analysis/BIN_ANALYSIS_REPORT.md)
- [Project Structure Report](docs/analysis/PROJECT_STRUCTURE_REPORT.md)

### Change Logs
See [docs/changes/](docs/changes/) for detailed update history.

## 🔒 Security

⚠️ **Important Security Notes:**

1. Never commit `.env` files
2. Rotate credentials regularly
3. Use strong database passwords
4. Restrict webhook endpoint access (IP whitelist recommended)
5. Keep dependencies updated
6. Monitor logs for suspicious activity

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u webhook-receiver.service -n 50

# Check if port is in use
sudo lsof -i :8000

# Verify database connection
psql -U webhook_user -d payment_transactions -c "SELECT 1"
```

### No alerts being sent

```bash
# Check monitor is running
ps aux | grep payment_monitor

# Check crontab
crontab -l | grep payment_monitor

# Test Telegram manually
python3 utils/test_telegram.py
```

### Database connection issues

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U webhook_user -d payment_transactions -h localhost

# View database logs
sudo journalctl -u postgresql -f
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (when test suite is available)
5. Submit a pull request

## 📊 Project Stats

- **Application Files**: 3 main Python files
- **Utility Scripts**: 6 helper scripts
- **SQL Files**: 14 database files
- **Documentation**: 19 markdown files
- **Total Transactions Processed**: 286K+
- **Webhook Events Logged**: 373K+
- **BINs Mapped**: 1,103
- **Merchants Tracked**: 84

## 📜 License

Proprietary - All rights reserved

## 👤 Author

Anil Sanal

## 📞 Support

For issues or questions:
- Check [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)
- Review logs: `tail -f /var/log/webhook_receiver.log`
- Contact: [your-email]

---

**Last Updated**: 2025-01-11
**Version**: 2.1.0
**Status**: Production Ready ✅
