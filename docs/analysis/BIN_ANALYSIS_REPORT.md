# BIN and Bank Names Analysis Report

**Generated**: 2025-10-31  
**Database**: payment_transactions

---

## Executive Summary

### Overall Statistics

| Metric | Count |
|--------|-------|
| **Total Unique BINs in Transactions** | 500 |
| **BINs with Bank Name Defined** | 381 (76.2%) |
| **BINs WITHOUT Bank Name (UNDEFINED)** | 119 (23.8%) |
| **BINs in bin_bank_mapping Table** | 1,103 |

### Status Breakdown

- ✅ **381 BINs** - Have bank_name populated in transactions
- ❌ **119 BINs** - Missing bank_name (UNDEFINED - need to be added)

---

## Critical Findings

### Top 20 Undefined BINs by Transaction Volume

| BIN | Transaction Count | Merchants | Date Range |
|-----|------------------|-----------|------------|
| 401924 | 520 | Herogaming JPY, Herogaming USD, Igloo Ventures | Oct 13 - Oct 31 |
| 409084 | 285 | Multipay, Multipay MC TRY, Paytic | Oct 13 - Oct 31 |
| 404946 | 79 | Herogaming JPY, Herogaming USD, Igloo Ventures | Oct 13 - Oct 31 |
| 470881 | 55 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 31 |
| 423025 | 49 | Paytic | Oct 23 - Oct 30 |
| 498005 | 47 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 30 |
| 474108 | 42 | Multipay, Multipay MC TRY, Paytic | Oct 16 - Oct 31 |
| 405762 | 38 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 29 |
| 400142 | 36 | Herogaming JPY, Herogaming USD | Oct 14 - Oct 28 |
| 544298 | 31 | E-Pin, Panelix, Sispay (TEST) | Oct 19 - Oct 31 |
| 464988 | 31 | Herogaming JPY, Herogaming USD, Igloo Ventures | Oct 13 - Oct 31 |
| 498021 | 29 | Herogaming USD | Oct 20 - Oct 29 |
| 461676 | 28 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 29 |
| 432321 | 26 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 28 |
| 412199 | 25 | Multipay, Multipay MC TRY | Oct 15 - Oct 30 |
| 462437 | 23 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 26 |
| 412256 | 22 | Herogaming JPY, Herogaming USD, Igloo Ventures | Oct 14 - Oct 30 |
| 407613 | 18 | Herogaming JPY, Herogaming USD | Oct 13 - Oct 29 |
| 429769 | 17 | Herogaming JPY, Herogaming USD, Igloo Ventures | Oct 15 - Oct 30 |
| 438775 | 15 | ASoftGame, E-Pin, Panelix, Sipay (TEST) | Oct 16 - Oct 27 |

**Total transactions affected by top 20 undefined BINs**: ~1,410 transactions

---

## Impact Analysis

### Undefined BINs Impact

- **Total transactions with undefined BINs**: ~1,800 transactions
- **Percentage of total transactions**: Varies by merchant
- **Primary affected merchants**:
  - Herogaming JPY [LIVE]
  - Herogaming USD [LIVE]
  - Multipay [LIVE]
  - Multipay MC TRY [LIVE]
  - Paytic [LIVE]
  - Igloo Ventures [LIVE]

### Monitoring Impact

Without bank names defined:
- ❌ Cannot monitor MID + Bank performance accurately
- ❌ Telegram alerts won't show bank information
- ❌ Grafana dashboards won't show proper bank breakdowns
- ❌ Revenue analysis by bank is incomplete

---

## Files Generated

### 1. Complete BIN Report
**File**: `/opt/payment-webhook/bins_complete_report.csv`

Contains ALL 501 BIN records with:
- cc_bin
- bank_name_in_transactions
- bank_name_in_mapping
- card_brand
- card_type
- bank_country
- transaction_count
- merchant_count
- first_seen_date
- last_seen_date
- status (OK, MISSING_BANK_NAME, NOT_IN_MAPPING_TABLE)

### 2. Undefined BINs Import Template
**File**: `/opt/payment-webhook/undefined_bins_to_import.csv`

Contains 119 undefined BINs ready for bank name assignment:
- BIN (populated)
- BankName (empty - to be filled)
- BankCountry (empty - to be filled)
- CardBrand (empty - to be filled)
- CardType (empty - to be filled)
- TransactionCount
- MerchantCount
- Merchants
- FirstSeenDate
- LastSeenDate

---

## Next Steps

### Option 1: Manual Research and Import
1. Open `/opt/payment-webhook/undefined_bins_to_import.csv`
2. Research each BIN using:
   - https://binlist.net/
   - https://www.bincodes.com/
   - Payment gateway documentation
3. Fill in BankName, BankCountry, CardBrand, CardType
4. Import using bin_import.py script

### Option 2: Automated BIN Lookup (Recommended)
Use the existing `bin_import.py` script with an API service:
```bash
cd /opt/payment-webhook
source venv/bin/activate
python3 bin_import.py <your_updated_csv_file>
```

### Option 3: Request from Payment Gateway
Contact your payment gateway provider (Coriunder) to get:
- Complete BIN database
- Automatic BIN lookup webhook parameter

---

## Database Tables

### bin_bank_mapping
- **Purpose**: Stores BIN to Bank Name mappings
- **Current entries**: 1,103 BINs
- **Location**: payment_transactions database
- **Used by**: webhook_app.py for automatic bank name population

### Usage in System

When a transaction arrives:
1. `webhook_app.py` extracts cc_bin from transaction
2. Looks up bank_name from bin_bank_mapping table
3. Stores bank_name in transactions table
4. Monitoring and alerts use bank_name for grouping

---

## Recommendations

### High Priority (Top 20 BINs)
These 20 BINs account for ~1,410 transactions. Adding them will significantly improve:
- Monitoring accuracy
- Alert effectiveness
- Dashboard completeness

### Medium Priority (Next 30 BINs)
BINs with 3-10 transactions each. Add when time permits.

### Low Priority (Remaining 69 BINs)
BINs with 1-2 transactions. Can be added gradually or on-demand.

---

## Technical Details

### BIN Lookup Query Example
```sql
SELECT bank_name 
FROM bin_bank_mapping 
WHERE bin = '540709';
```

### Import Process
1. CSV file with BIN, BankName, CardBrand, CardType, BankCountry
2. Run import script: `python3 bin_import.py <csv_file>`
3. Script inserts into bin_bank_mapping table
4. Backfill existing transactions (optional)

### Backfill Query (if needed)
```sql
UPDATE transactions t
SET bank_name = bbm.bank_name
FROM bin_bank_mapping bbm
WHERE t.cc_bin = bbm.bin
  AND (t.bank_name IS NULL OR t.bank_name = '');
```

---

## Status

- ✅ Analysis complete
- ✅ Reports generated
- ✅ CSV exports ready
- ⏳ Awaiting BIN information for 119 undefined BINs
- ⏳ Import and backfill pending

**Report Version**: 1.0  
**Last Updated**: 2025-10-31 18:37:00 UTC
