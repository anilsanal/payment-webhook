# Quick Reference - BIN Data Management

## Location
**Project**: `/opt/payment-webhook/`
**Database**: `payment_transactions` (PostgreSQL, localhost:5432)
**Credentials**: See `.env` file (webhook_user:yingyanganil5s)

## Key Paths

### Core BIN Files
- `/opt/payment-webhook/bin_import.py` - BIN data importer script
- `/opt/payment-webhook/BINS_and_BANKS_List.csv` - Main BIN source (1,303 records)
- `/opt/payment-webhook/undefined_bins_to_import.csv` - Template for missing 119 BINs
- `/opt/payment-webhook/bins_complete_report.csv` - Analysis of all 501 BINs

### Database Tables
- `bin_bank_mapping` - Master BIN-to-bank mapping (1,103 records)
- `transactions` - Transaction records (286,465) with cc_bin and bank_name
- `webhook_events` - Audit trail (373,812 records)

### Application Code
- `/opt/payment-webhook/webhook_app.py` - Main service (port 8000)
- `/opt/payment-webhook/payment_monitor.py` - Monitoring daemon
- `/opt/payment-webhook/merchant_reimport.py` - Data update example

## Quick Commands

### Import BIN Data
```bash
cd /opt/payment-webhook
source venv/bin/activate
python3 bin_import.py BINS_and_BANKS_List.csv
```

### Check BIN Status
```bash
psql -U webhook_user -d payment_transactions -c "SELECT COUNT(*) FROM bin_bank_mapping;"
psql -U webhook_user -d payment_transactions -c "SELECT COUNT(*) FROM transactions WHERE bank_name IS NULL;"
```

### Backup Before Update
```bash
sudo -u postgres pg_dump payment_transactions -t bin_bank_mapping > backup_bin_$(date +%s).sql
sudo -u postgres pg_dump payment_transactions -t transactions > backup_trans_$(date +%s).sql
```

### Backfill Existing Transactions
```sql
UPDATE transactions t
SET bank_name = bbm.bank_name
FROM bin_bank_mapping bbm
WHERE t.cc_bin = bbm.bin AND t.bank_name IS NULL;
```

### Check Service
```bash
systemctl status webhook-receiver
journalctl -u webhook-receiver -f
curl http://localhost:8000/health
```

## Current Status

| Item | Count | Status |
|------|-------|--------|
| Total Transactions | 286,465 | OK |
| Total BINs in Table | 1,103 | OK |
| Active BINs (in use) | 513 | OK |
| Undefined BINs | 119 | NEEDS UPDATE |
| Transactions with bank_name | 239,421 (83.6%) | GOOD |
| Transactions without bank_name | 47,044 (16.4%) | NEEDS DATA |

## Top Priority: Add These 20 BINs
```
401924, 409084, 404946, 470881, 423025, 498005, 474108, 405762, 400142, 544298
464988, 498021, 461676, 432321, 412199, 462437, 412256, 407613, 429769, 438775
```
These cover 1,410 transactions (3.9% of total)

## Important Files to Know

1. **BIN_ANALYSIS_REPORT.md** - Detailed analysis with recommendations
2. **undefined_bins_to_import.csv** - Template ready for data entry
3. **PROJECT_STRUCTURE_REPORT.md** - Comprehensive technical documentation
4. **database_schema_fixed.sql** - Current DB schema

## Security Alert
Plain text credentials in:
- `.env` file
- Python scripts (hardcoded passwords)

Recommend: Rotate password and use environment variables

## Testing Import
1. Create test CSV with sample BINs
2. Run: `python3 bin_import.py test.csv`
3. Verify: `SELECT * FROM bin_bank_mapping LIMIT 5;`
4. Check transactions: `SELECT COUNT(*) FROM transactions WHERE bank_name IS NOT NULL;`

## Rollback After Import
```bash
# Restore from backup if needed
psql -U webhook_user -d payment_transactions -f backup_bin_12345678.sql
```

## More Info
See `/opt/payment-webhook/PROJECT_STRUCTURE_REPORT.md` for full documentation
