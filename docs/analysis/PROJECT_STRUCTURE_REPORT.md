# Payment Webhook System - Comprehensive Project Structure & BIN Data Management Report

**Report Generated**: 2025-11-03  
**System**: Payment Gateway Webhook Receiver for Transaction Monitoring  
**Database**: PostgreSQL (payment_transactions)  
**Server Location**: /opt/payment-webhook

---

## EXECUTIVE SUMMARY

This is a FastAPI-based payment transaction webhook receiver system that processes payment gateway transactions and stores them in PostgreSQL. The system has a specific focus on Bank Identification Number (BIN) to Bank Name mapping for transaction monitoring and dashboard analytics.

### Key Statistics
- **Total Transactions**: 286,465 records
- **Total Webhook Events**: 373,812 (audit trail)
- **Unique BINs Used**: 513 (active in transactions)
- **BINs in Mapping Table**: 1,103 total
- **BINs Missing Bank Names**: 119 (23.8% of active BINs)
- **Transactions Without Bank Names**: 47,044 (16.4% of transactions)

---

## PROJECT STRUCTURE

### Base Directory
```
/opt/payment-webhook/
├── Python Application Files
├── Database Files (SQL schemas, migrations, views)
├── Data Import Files (CSV)
├── Documentation (MD files)
├── Configuration Files (.env)
├── Virtual Environment (venv/)
└── Logs (/var/log/)
```

### All Project Files

#### Python Scripts (Executable)
| File | Purpose | Size | Key Function |
|------|---------|------|--------------|
| `/opt/payment-webhook/webhook_app.py` | **Main webhook receiver service** - FastAPI app listening for webhooks | 23.8 KB | Receives transaction webhooks, validates data, stores in DB, performs BIN/merchant name lookups |
| `/opt/payment-webhook/bin_import.py` | **BIN data importer** - Loads BIN-to-bank mappings | 2.7 KB | Reads CSV, imports to bin_bank_mapping table, handles conflicts |
| `/opt/payment-webhook/payment_monitor.py` | **Monitoring & alerting daemon** - Checks for payment issues | 25.2 KB | Monitors decline rates, sends Telegram/Slack alerts, groups by bank_name |
| `/opt/payment-webhook/mid_import.py` | **Terminal ID importer** - Loads MidID to name mappings | 3.6 KB | Imports MidID mappings, flexible CSV header detection |
| `/opt/payment-webhook/merchant_reimport.py` | **Merchant data reimporter** - Updates merchant mappings | 2.6 KB | Clears & reimports merchant data, backfills transactions |
| `/opt/payment-webhook/backfill_mid_names.py` | **Backfill script** - Updates existing records with names | 5.1 KB | Updates webhook_events & transactions with mid_name lookups |
| `/opt/payment-webhook/telegram_setup.py` | **Telegram integration setup** | 6.2 KB | Configures Telegram bot for alerts |
| `/opt/payment-webhook/test_telegram.py` | **Telegram testing utility** | 2.1 KB | Tests Telegram bot connectivity |

#### Database Schema & Migration Files (SQL)
| File | Purpose | Type |
|------|---------|------|
| `/opt/payment-webhook/database_schema.sql` | **Primary database schema** - Creates core tables | Initial Schema (7.9 KB) |
| `/opt/payment-webhook/database_schema_fixed.sql` | **Updated schema** - Fixed version with additional fields | Current Schema (8.6 KB) |
| `/opt/payment-webhook/migration_add_mid_name.sql` | Adds mid_name field to webhook_events & transactions | Migration (1.6 KB) |
| `/opt/payment-webhook/migration_add_midid_reconid.sql` | Adds mid_id and recon_id fields | Migration (2.2 KB) |
| `/opt/payment-webhook/create_grafana_views.sql` | Creates views for Grafana dashboards | Views (7.7 KB) |
| `/opt/payment-webhook/create_bank_performance_views.sql` | **Bank performance analysis views** | Views (6.6 KB) |
| `/opt/payment-webhook/create_alltime_views.sql` | All-time statistics views | Views (8.5 KB) |
| `/opt/payment-webhook/create_monitoring_views.sql` | Monitoring-specific views | Views (7.0 KB) |
| `/opt/payment-webhook/create_revenue_views.sql` | Revenue analysis views | Views (6.4 KB) |
| `/opt/payment-webhook/create_mid_mapping_table.sql` | Creates mid_mapping table | DDL (1.3 KB) |
| `/opt/payment-webhook/merchant_import.sql` | Merchant mapping table & initial data | DDL with Data (3.5 KB) |
| `/opt/payment-webhook/fix_merchant_data.sql` | Merchant data corrections | Maintenance (2.3 KB) |
| `/opt/payment-webhook/update_grafana_views.sql` | Updates Grafana view definitions | Maintenance (7.1 KB) |

#### Data Files (CSV)
| File | Purpose | Records | Key Fields |
|------|---------|---------|-----------|
| `/opt/payment-webhook/BINS_and_BANKS_List.csv` | **Main BIN import file** - Source of bank mappings | 1,303 rows | BIN, BankName, CardScheme |
| `/opt/payment-webhook/undefined_bins_to_import.csv` | **Template for missing BINs** - Ready to fill in | 119 rows | BIN (only), + empty fields for data entry |
| `/opt/payment-webhook/bins_complete_report.csv` | **Comprehensive BIN analysis report** - Generated analysis | 501 rows | Full BIN details with status |
| `/opt/payment-webhook/Merchant - 20251011112853.csv` | Merchant master data | 84 merchants | merchant_id, merchant_name |
| `/opt/payment-webhook/Terminal_MidIDs.csv` | Terminal/MID master data | 2.2 KB | MidID, terminal_name |

#### Configuration Files
| File | Contains |
|------|----------|
| `/opt/payment-webhook/.env` | **Database credentials, API tokens** (PostgreSQL, Telegram, Slack) |
| `/opt/payment-webhook/requirements.txt` | Python dependencies (FastAPI, psycopg2, uvicorn, etc.) |
| `/opt/payment-webhook/install.sh` | Automated installation & systemd setup |

#### Documentation
| File | Purpose |
|------|---------|
| `/opt/payment-webhook/BIN_ANALYSIS_REPORT.md` | **Critical**: Detailed BIN mapping status & recommendations |
| `/opt/payment-webhook/BANK_PERFORMANCE_VIEWS.md` | Bank-focused analytics documentation |
| `/opt/payment-webhook/GRAFANA_SETUP.md` | Grafana dashboard configuration |
| `/opt/payment-webhook/GRAFANA_DASHBOARD_UPDATES.md` | Dashboard update history |
| `/opt/payment-webhook/MONITORING_README.md` | Payment monitoring setup |
| (Additional MD files) | Various fixes, guides, and cleanup docs |

#### Log Files
| Location | Purpose |
|----------|---------|
| `/var/log/webhook_receiver.log` | Application logs |
| `/var/log/webhook_receiver_error.log` | Error logs |

#### Backup Files
| File | Purpose |
|------|---------|
| `/opt/payment-webhook/views_backup_20251029_180333.sql` | Views backup before migration |
| `/opt/payment-webhook/views_backup_before_trans_datetime_migration.sql` | Pre-migration backup |
| `/opt/payment-webhook/bin_analysis_reports.tar.gz` | Compressed BIN reports archive |

---

## DATABASE SCHEMA

### Core Tables for BIN Management

#### 1. `bin_bank_mapping` TABLE
**Purpose**: Central BIN-to-bank name mapping repository

```
Column Name     | Type              | Constraints      | Indexes
----------------|-------------------|------------------|----------
id              | SERIAL PRIMARY KEY|                  | PRIMARY
bin             | VARCHAR(10)       | UNIQUE NOT NULL  | UNIQUE
bank_name       | VARCHAR(255)      | NOT NULL         | idx_bank_name_lookup
bank_country    | VARCHAR(10)       | NULL             |
card_type       | VARCHAR(50)       | NULL             |
card_brand      | VARCHAR(50)       | NULL             |
notes           | TEXT              | NULL             |
created_at      | TIMESTAMP         | DEFAULT NOW()    |
updated_at      | TIMESTAMP         | DEFAULT NOW()    |
```

- **Current Entries**: 1,103 unique BINs
- **Usage**: Referenced by webhook_app.py to resolve bank_name for incoming transactions
- **Import Method**: bin_import.py script

#### 2. `transactions` TABLE
**Purpose**: Stores latest status of each unique transaction

Relevant BIN-related columns:
```
Column Name     | Type              | Notes
----------------|-------------------|------
cc_bin          | VARCHAR(10)       | Card BIN (first 6 digits) - indexed
bank_name       | VARCHAR(255)      | Resolved from bin_bank_mapping
```

- **Total Records**: 286,465 transactions
- **Transactions with NULL bank_name**: 47,044 (16.4%)
- **Unique BINs in this table**: 513

#### 3. `webhook_events` TABLE
**Purpose**: Audit trail - stores every webhook received

Relevant columns (same as transactions for bank data):
```
cc_bin          | VARCHAR(10)       | Indexed
bank_name       | VARCHAR(255)      | Indexed
```

- **Total Records**: 373,812 webhook events
- **Purpose**: Full history even if transaction is updated multiple times

#### 4. Supporting Mapping Tables

**merchant_mapping** - Merchant ID to name (84 merchants)
- Used by webhook_app.py to populate merchant_name field

**mid_mapping** - Terminal/MidID to name mapping
- Used for terminal name lookups in monitoring

### Database Connection Details

```
Database Name:  payment_transactions
Database User:  webhook_user
Database Host:  localhost
Database Port:  5432
```

**Connection Config Location**: 
- `.env` file in `/opt/payment-webhook/`
- Hardcoded in Python scripts (DB_CONFIG dict)

---

## BIN (BANK IDENTIFICATION NUMBER) DATA MANAGEMENT

### How BIN Data Flows Through the System

```
1. INCOMING WEBHOOK (payment transaction)
   ↓
2. webhook_app.py extracts cc_bin field
   ↓
3. Queries bin_bank_mapping table for bank_name
   ↓
4. Stores transaction in:
   - webhook_events (audit trail)
   - transactions (latest status)
   ↓
5. Used by:
   - payment_monitor.py (grouping alerts by bank)
   - Grafana dashboards (bank performance views)
   - Analytics queries
```

### Current BIN Data Status

**Total Active BINs**: 513 (used in recent transactions)
**BINs in Mapping Table**: 1,103 (1,103 - 513 = 590 unused)
**Missing Bank Names**: 119 BINs (23.8% of active)

**Impact of Missing Bank Names**:
- 47,044 transactions (~16.4%) cannot be grouped by bank
- Monitoring alerts won't show bank information
- Grafana dashboards show "undefined" or NULL for bank
- Revenue analysis by bank is incomplete

### Top 20 Undefined BINs

| BIN | Transactions | Merchants | Date Range | Volume |
|-----|---|---|---|---|
| 401924 | 520 | 3 | Oct 13-31 | HIGH |
| 409084 | 285 | 3 | Oct 13-31 | HIGH |
| 404946 | 79 | 3 | Oct 13-31 | MEDIUM |
| 470881 | 55 | 2 | Oct 13-31 | MEDIUM |
| 423025 | 49 | 1 | Oct 23-30 | MEDIUM |
| (15 more...) | | | | |

**Total Top 20 Impact**: ~1,410 transactions (3.9% of all transactions)

### BIN Import Sources

1. **Primary File**: `/opt/payment-webhook/BINS_and_BANKS_List.csv`
   - Contains 1,303 BIN records
   - Format: BIN, BankName, CardScheme
   - Last updated: Oct 13, 2025

2. **Undefined BINs Template**: `/opt/payment-webhook/undefined_bins_to_import.csv`
   - Template with 119 BINs needing data
   - Fields ready for manual or automated population
   - Columns: BIN, BankName, BankCountry, CardBrand, CardType, TransactionCount, MerchantCount, Merchants, FirstSeenDate, LastSeenDate

3. **Reference Report**: `/opt/payment-webhook/bins_complete_report.csv`
   - Complete analysis of all BINs
   - Shows mapping status and transaction volume
   - Updated Oct 31, 2025

---

## KEY APPLICATION CODE

### webhook_app.py - Main Application

**Key Functions**:

1. **Bank Name Lookup**
```python
def get_bank_name(ccbin, cursor):
    """Get bank name from BIN mapping table"""
    cursor.execute(
        "SELECT bank_name FROM bin_bank_mapping WHERE bin = %s",
        (ccbin,)
    )
    result = cursor.fetchone()
    return result['bank_name'] if result else None
```

2. **Webhook Reception & Storage**
```python
@app.api_route("/webhook", methods=["GET", "POST"])
async def receive_webhook(request: Request):
    # Parses webhook data
    # Validates required fields
    # Looks up bank_name from BIN
    # Stores in webhook_events (audit)
    # Upserts in transactions (latest status)
```

3. **Transaction Insertion with Bank Data**
```python
def insert_webhook_event(data, status, cursor):
    # Gets bank_name from bin_bank_mapping
    # Inserts into webhook_events with bank_name
    # Also inserts merchant_name, mid_name from other mappings
```

### bin_import.py - BIN Data Import

```python
def import_bin_data(csv_file_path):
    # Reads CSV file (BIN, BankName, CardScheme)
    # Clears existing data: DELETE FROM bin_bank_mapping
    # Inserts with ON CONFLICT handler (UPSERT)
    # Reports import statistics
```

**Command**:
```bash
python3 /opt/payment-webhook/bin_import.py /path/to/BINS_and_BANKS_List.csv
```

### payment_monitor.py - Monitoring with Bank Data

Uses `bank_name` for:
- Grouping transactions by bank for decline rate analysis
- Filtering alerts by bank + terminal (MidID)
- Telegram notifications showing bank information
- Decline reason analysis per bank

---

## DATA IMPACT ANALYSIS

### What Happens Without Complete BIN Mapping

1. **Incomplete Transactions**
   - 47,044 transactions stored with NULL bank_name
   - Cannot filter by bank in dashboards
   - Cannot group by bank + terminal for monitoring

2. **Broken Monitoring Alerts**
   - Payment monitor skips transactions with undefined banks
   - Alerts won't show which bank has issues
   - Incomplete decline rate calculations

3. **Dashboard Gaps**
   - Grafana views with "WHERE bank_name IS NOT NULL" skip 16.4% of data
   - Bank performance views incomplete
   - Revenue by bank analysis missing data

4. **Analytics Impact**
   - Reports underreport transaction volumes
   - Bank-specific trends hidden
   - Merchant performance per bank unknown

---

## MIGRATION & BACKUP STRATEGY

### Migration Scripts (Applied in Order)

1. **Initial Schema**: `database_schema.sql` or `database_schema_fixed.sql`
   - Creates webhook_events, transactions, bin_bank_mapping tables

2. **Add MidID/ReconID**: `migration_add_midid_reconid.sql`
   - Adds mid_id, recon_id, merchant_name columns

3. **Add MID Names**: `migration_add_mid_name.sql`
   - Adds mid_name column

4. **Create Views**: Various `create_*_views.sql` scripts
   - Build Grafana/Metabase views

### View Dependencies on bank_name

All these views use `bank_name` for grouping and filtering:
- create_bank_performance_views.sql
- create_alltime_views.sql
- create_monitoring_views.sql

**Important**: Views filter out NULL bank_name with `WHERE bank_name IS NOT NULL`

### Backup Strategy

**View Backups Before Major Changes**:
```bash
pg_dump -U webhook_user payment_transactions -t public.* > views_backup_$(date +%s).sql
```

**Data Backups**:
- `/opt/payment-webhook/views_backup_20251029_180333.sql` - Recent backup
- `/opt/payment-webhook/bin_analysis_reports.tar.gz` - Analysis exports

---

## SAFE BIN DATA UPDATE PROCEDURE

### Step 1: Analyze Current State
```bash
cd /opt/payment-webhook
source venv/bin/activate

# Check current BINs
python3 -c "
import psycopg2
conn = psycopg2.connect(dbname='payment_transactions', user='webhook_user', password='yingyanganil5s', host='localhost')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM bin_bank_mapping')
print(f'Current BINs: {cursor.fetchone()[0]}')
cursor.close()
"
```

### Step 2: Prepare Update File
```
Option A: Update undefined_bins_to_import.csv with missing bank names
Option B: Use external BIN database API
Option C: Request from payment gateway provider
```

### Step 3: Backup Current Data
```bash
# Backup bin_bank_mapping table
sudo -u postgres pg_dump payment_transactions -t bin_bank_mapping > /opt/payment-webhook/backup_bin_bank_mapping_$(date +%Y%m%d).sql

# Backup transactions table
sudo -u postgres pg_dump payment_transactions -t transactions > /opt/payment-webhook/backup_transactions_$(date +%Y%m%d).sql
```

### Step 4: Import BIN Data
```bash
cd /opt/payment-webhook
source venv/bin/activate
python3 bin_import.py /path/to/updated_bins.csv
```

### Step 5: Backfill Existing Transactions (Optional)
```sql
-- Update transactions with newly imported bank names
UPDATE transactions t
SET bank_name = bbm.bank_name
FROM bin_bank_mapping bbm
WHERE t.cc_bin = bbm.bin
  AND (t.bank_name IS NULL OR t.bank_name = '');

-- Verify
SELECT COUNT(*) FROM transactions WHERE bank_name IS NULL;
```

### Step 6: Verify Results
```bash
# Check if import successful
python3 -c "
import psycopg2
conn = psycopg2.connect(dbname='payment_transactions', user='webhook_user', password='yingyanganil5s', host='localhost')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM bin_bank_mapping')
print(f'New BIN count: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM transactions WHERE bank_name IS NOT NULL')
print(f'Transactions with bank names: {cursor.fetchone()[0]}')
cursor.close()
"
```

### Step 7: Test Monitoring & Dashboards
- Run payment_monitor.py
- Check Grafana bank performance views
- Verify alerts include bank information

---

## SERVICE MANAGEMENT

### Systemd Service
**File**: `/etc/systemd/system/webhook-receiver.service`

**Commands**:
```bash
# Start/stop service
sudo systemctl start webhook-receiver
sudo systemctl stop webhook-receiver
sudo systemctl restart webhook-receiver

# View logs
sudo journalctl -u webhook-receiver -f

# Check status
sudo systemctl status webhook-receiver
```

### Application Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

---

## SECURITY NOTES

### Exposed Credentials in Files
⚠️ **SECURITY ALERT**: Database credentials are stored in plain text:
- `/opt/payment-webhook/.env` (contains DB_PASSWORD, API tokens)
- `/opt/payment-webhook/bin_import.py` (hardcoded in DB_CONFIG)
- `/opt/payment-webhook/webhook_app.py` (default password)
- `/opt/payment-webhook/*.py` scripts (hardcoded credentials)

**Current Credentials**:
```
DB_USER: webhook_user
DB_PASSWORD: yingyanganil5s  # Plain text!
Telegram Token: 8237771288:AAFvEX6RDJzID5KoPITr62SsCcYm39HSmlw  # In .env
Slack Webhook: In .env file
```

### Recommendations
1. Rotate database password immediately
2. Move credentials to environment variables or secrets manager
3. Restrict file permissions on .env file
4. Audit access logs for these files

---

## DEPENDENCIES & REQUIREMENTS

**Python Package Requirements** (`requirements.txt`):
```
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
psycopg2-binary==2.9.9   # PostgreSQL adapter
python-multipart==0.0.6  # Form parsing
python-dotenv==1.0.0     # Environment variables
requests==2.31.0         # HTTP client (for Slack/Telegram)
```

**System Requirements**:
- Python 3.12+
- PostgreSQL 12+
- 2GB+ RAM (for transaction table with 286K records)
- Nginx (optional, for reverse proxy)
- Metabase/Grafana (optional, for dashboards)

---

## RECOMMENDATIONS FOR BIN DATA UPDATE

### Immediate Actions (High Priority)
1. **Add Top 20 Undefined BINs**
   - These account for ~1,410 transactions (3.9%)
   - Research using https://binlist.net/ or https://www.bincodes.com/
   - Estimated effort: 1-2 hours for manual research
   - Impact: Immediate improvement in monitoring accuracy

2. **Backup Current Data**
   - Create backup before any changes
   - Store in safe location with versioning

3. **Test Import Process**
   - Test bin_import.py with test CSV first
   - Verify transactions table updates correctly

### Medium Priority
4. **Implement Automated BIN Lookup**
   - Consider BIN lookup API service (many free options available)
   - Would automate future updates

5. **Update Monitoring Queries**
   - Ensure payment_monitor.py handles undefined banks gracefully
   - Add alerts for undefined BINs

### Long-term
6. **Request Complete BIN DB from Gateway**
   - Contact Coriunder (payment gateway) for complete BIN list
   - Ask for automatic BIN resolution in webhook parameters

7. **Implement BIN Caching**
   - Cache lookups to reduce database queries

---

## FILE MANIFEST

### Complete File Listing
```
/opt/payment-webhook/
├── Application Files:
│   ├── webhook_app.py (23.8 KB) - Main FastAPI service
│   ├── payment_monitor.py (25.2 KB) - Monitoring daemon
│   ├── bin_import.py (2.7 KB) - BIN importer
│   ├── mid_import.py (3.6 KB) - Terminal importer
│   ├── merchant_reimport.py (2.6 KB) - Merchant importer
│   ├── backfill_mid_names.py (5.1 KB) - Name backfiller
│   ├── telegram_setup.py (6.2 KB) - Telegram config
│   └── test_telegram.py (2.1 KB) - Telegram test
│
├── Database Files (SQL):
│   ├── database_schema.sql (7.9 KB) - Initial schema
│   ├── database_schema_fixed.sql (8.6 KB) - Updated schema
│   ├── migration_add_midid_reconid.sql (2.2 KB)
│   ├── migration_add_mid_name.sql (1.6 KB)
│   ├── create_bank_performance_views.sql (6.6 KB)
│   ├── create_alltime_views.sql (8.5 KB)
│   ├── create_monitoring_views.sql (7.0 KB)
│   ├── create_revenue_views.sql (6.4 KB)
│   ├── create_grafana_views.sql (7.7 KB)
│   ├── create_mid_mapping_table.sql (1.3 KB)
│   ├── merchant_import.sql (3.5 KB)
│   ├── fix_merchant_data.sql (2.3 KB)
│   └── update_grafana_views.sql (7.1 KB)
│
├── Data Files (CSV):
│   ├── BINS_and_BANKS_List.csv (54 KB) - Main BIN source
│   ├── undefined_bins_to_import.csv (9.1 KB) - Template
│   ├── bins_complete_report.csv (46 KB) - Analysis
│   ├── Merchant - 20251011112853.csv (2.2 KB)
│   └── Terminal_MidIDs.csv (2.2 KB)
│
├── Configuration:
│   ├── .env (564 bytes) - Credentials & API keys
│   ├── requirements.txt (128 bytes) - Dependencies
│   └── install.sh (6.8 KB) - Installation script
│
├── Documentation:
│   ├── BIN_ANALYSIS_REPORT.md (6.0 KB) - **CRITICAL**
│   ├── BANK_PERFORMANCE_VIEWS.md (8.4 KB)
│   ├── GRAFANA_SETUP.md (7.5 KB)
│   └── (Additional MD files for guides)
│
├── Backups & Archives:
│   ├── views_backup_20251029_180333.sql (50 KB)
│   ├── bin_analysis_reports.tar.gz (9.8 KB)
│   └── (Additional backup files)
│
├── Virtual Environment:
│   └── venv/ (directory)
│
└── Logs (in /var/log/):
    ├── webhook_receiver.log
    └── webhook_receiver_error.log
```

---

## DATABASE STATISTICS (as of 2025-11-03)

| Metric | Value |
|--------|-------|
| Total Transactions | 286,465 |
| Total Webhook Events | 373,812 |
| Unique BINs in Use | 513 |
| BINs in Mapping Table | 1,103 |
| Undefined BINs | 119 |
| Transactions with bank_name | 239,421 (83.6%) |
| Transactions without bank_name | 47,044 (16.4%) |
| BINs with Complete Mapping | 381 (76.2%) |
| Merchants Configured | 84 |
| Terminals/MIDs Configured | ? |

---

## CONTACT & SUPPORT

For BIN data updates:
1. Review `/opt/payment-webhook/BIN_ANALYSIS_REPORT.md` for detailed guidance
2. Execute `/opt/payment-webhook/bin_import.py` with updated CSV
3. Run backfill scripts to update existing transactions
4. Verify with queries to check bank_name population

For system monitoring:
- Check `/var/log/webhook_receiver.log` for real-time activity
- Monitor `payment_monitor.py` daemon for alert status
- Access Grafana/Metabase for dashboards

---

**Report End**
