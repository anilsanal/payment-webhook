-- =================================================================
-- FIX MERCHANT DATA ISSUES
-- This script fixes duplicate mappings and updates transaction names
-- =================================================================

BEGIN;

-- ========================================
-- 1. Remove duplicate Gantenpay mapping
-- ========================================
-- Keep 4316065 (has 5 transactions), remove 9611509 (has 0 transactions)
DELETE FROM merchant_mapping
WHERE merchant_id = '9611509'
  AND merchant_name = '[ACQ] Gantenpay LIVE';

SELECT 'Removed duplicate Gantenpay mapping (9611509)' as status;

-- ========================================
-- 2. Update all transactions to use correct merchant names from mapping
-- ========================================
-- This will fix all inconsistent merchant names in the transactions table

UPDATE transactions t
SET merchant_name = m.merchant_name
FROM merchant_mapping m
WHERE t.merchant_id = m.merchant_id
  AND (t.merchant_name IS NULL OR t.merchant_name != m.merchant_name);

SELECT 'Updated transaction merchant names from mapping table' as status;

-- ========================================
-- 3. Show summary of fixes
-- ========================================
SELECT
    'Merchant Name Fixes' as fix_type,
    COUNT(*) as affected_rows
FROM transactions t
JOIN merchant_mapping m ON t.merchant_id = m.merchant_id;

-- ========================================
-- 4. Verify no more duplicates
-- ========================================
SELECT
    'Duplicate Check' as check_type,
    merchant_name,
    COUNT(DISTINCT merchant_id) as id_count,
    STRING_AGG(DISTINCT merchant_id, ', ') as merchant_ids
FROM merchant_mapping
GROUP BY merchant_name
HAVING COUNT(DISTINCT merchant_id) > 1;

-- ========================================
-- 5. Show current merchant distribution
-- ========================================
SELECT
    'Current Merchant Distribution' as report_type,
    m.merchant_name,
    COUNT(t.id) as transaction_count
FROM merchant_mapping m
LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
WHERE t.last_updated_at >= CURRENT_DATE
GROUP BY m.merchant_name
ORDER BY transaction_count DESC;

COMMIT;

SELECT '✅ All merchant data fixes completed successfully!' as final_status;
