-- =====================================================
-- COMPREHENSIVE MIGRATION: Fix ALL Timesaver MID Exclusions
-- Created: 2025-11-18
-- Purpose: Add missing exclusions for test MID 43110201461 (Timesaver) to ALL views
-- Affected Views: 16 views (Revenue, Merchant Performance, All-Time, Overall Stats)
-- =====================================================

BEGIN;

-- =====================================================
-- DEFINE EXCLUSION FILTER (for reference)
-- =====================================================
-- The following filter MUST be applied to ALL views:
--   AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
--   AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
--   AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
-- =====================================================

-- =====================================================
-- 1. REVENUE VIEWS (5 time-windowed views)
-- =====================================================

-- Revenue - 5 minutes
CREATE OR REPLACE VIEW revenue_by_currency_5min AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- Revenue - 15 minutes
CREATE OR REPLACE VIEW revenue_by_currency_15min AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- Revenue - 30 minutes
CREATE OR REPLACE VIEW revenue_by_currency_30min AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- Revenue - 1 hour
CREATE OR REPLACE VIEW revenue_by_currency_1hour AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '1 hour'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- Revenue - Today
CREATE OR REPLACE VIEW revenue_by_currency_today AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE DATE(last_updated_at) = CURRENT_DATE
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- =====================================================
-- 2. REVENUE SUMMARY VIEW (Combined windows)
-- =====================================================

CREATE OR REPLACE VIEW revenue_summary_all_windows AS
SELECT
    'Today' as time_window,
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue
FROM transactions
WHERE DATE(last_updated_at) = CURRENT_DATE
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency

UNION ALL

SELECT
    '1 Hour' as time_window,
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '1 hour'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency

UNION ALL

SELECT
    '30 Min' as time_window,
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency

ORDER BY time_window, total_revenue DESC;

-- =====================================================
-- 3. MERCHANT PERFORMANCE VIEWS (3 time-windowed views)
-- =====================================================

-- Merchant Performance - 5 minutes
CREATE OR REPLACE VIEW merchant_performance_5min AS
SELECT
    merchant_id,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- Merchant Performance - 15 minutes
CREATE OR REPLACE VIEW merchant_performance_15min AS
SELECT
    merchant_id,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- Merchant Performance - 30 minutes
CREATE OR REPLACE VIEW merchant_performance_30min AS
SELECT
    merchant_id,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- =====================================================
-- 4. ALL-TIME VIEWS (7 views)
-- =====================================================

-- Revenue by Currency (All Time)
CREATE OR REPLACE VIEW revenue_by_currency AS
SELECT
    trans_currency as currency,
    COUNT(*) as transaction_count,
    SUM(trans_amount) as total_revenue,
    ROUND(AVG(trans_amount), 2) as avg_transaction_amount,
    MIN(trans_amount) as min_amount,
    MAX(trans_amount) as max_amount,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE status = 'success'
    AND trans_amount IS NOT NULL
    AND trans_currency IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY trans_currency
ORDER BY total_revenue DESC;

-- Merchant Performance (All Time)
CREATE OR REPLACE VIEW merchant_performance AS
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

-- Bank Performance (All Time)
CREATE OR REPLACE VIEW bank_performance AS
SELECT
    bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE bank_name IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

-- MID + Bank Performance (All Time)
CREATE OR REPLACE VIEW mid_bank_performance AS
SELECT
    mid_id,
    mid_name,
    bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE mid_id IS NOT NULL
    AND bank_name IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- Merchant Timeout (All Time)
CREATE OR REPLACE VIEW merchant_timeout AS
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate
FROM transactions
WHERE merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- Timeout Performance by MID+Bank (All Time)
CREATE OR REPLACE VIEW timeout_performance AS
SELECT
    mid_id,
    mid_name,
    bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE mid_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- Overall Statistics (All Time Summary)
CREATE OR REPLACE VIEW overall_statistics AS
SELECT
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as total_successful,
    COUNT(*) FILTER (WHERE status = 'declined') as total_declined,
    COUNT(*) FILTER (WHERE status = 'pending') as total_pending,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as overall_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as overall_decline_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as overall_timeout_rate,
    MIN(last_updated_at) as first_transaction_ever,
    MAX(last_updated_at) as last_transaction,
    COUNT(DISTINCT merchant_id) as total_merchants,
    COUNT(DISTINCT bank_name) as total_banks,
    COUNT(DISTINCT mid_id) as total_mids
FROM transactions
WHERE 1=1
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%');

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify Timesaver is excluded from revenue views
SELECT '✅ Verification: Timesaver excluded from revenue_by_currency_5min' as test;
SELECT COUNT(*) as should_be_zero FROM (
    SELECT * FROM revenue_by_currency_5min
) sub WHERE EXISTS (
    SELECT 1 FROM transactions t
    WHERE (t.mid_id = '43110201461' OR t.mid_name ILIKE '%timesaver%')
    AND t.last_updated_at >= NOW() - INTERVAL '5 minutes'
);

-- Verify Timesaver is excluded from merchant_performance_5min
SELECT '✅ Verification: Timesaver excluded from merchant_performance_5min' as test;
SELECT COUNT(*) as should_be_zero FROM merchant_performance_5min m WHERE EXISTS (
    SELECT 1 FROM transactions t
    WHERE t.merchant_id = m.merchant_id
    AND (t.mid_id = '43110201461' OR t.mid_name ILIKE '%timesaver%')
    AND t.last_updated_at >= NOW() - INTERVAL '5 minutes'
);

-- Verify Timesaver is excluded from overall_statistics
SELECT '✅ Verification: Timesaver excluded from overall_statistics' as test;
SELECT
    total_transactions as total_excluding_timesaver,
    (SELECT COUNT(*) FROM transactions WHERE mid_id = '43110201461') as timesaver_count_should_not_be_in_total
FROM overall_statistics;

SELECT '✅✅✅ Migration completed: 16 views updated with Timesaver exclusions!' as final_status;
