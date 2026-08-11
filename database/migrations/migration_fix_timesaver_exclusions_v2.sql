-- =====================================================
-- COMPREHENSIVE MIGRATION: Fix ALL Timesaver MID Exclusions (V2)
-- Created: 2025-11-18
-- Purpose: Add missing exclusions for test MID 43110201461 (Timesaver) to ALL views
-- Note: Drops and recreates views to ensure proper column structure
-- Affected Views: 16 views (Revenue, Merchant Performance, All-Time, Overall Stats)
-- =====================================================

BEGIN;

-- =====================================================
-- DROP EXISTING VIEWS FIRST (to avoid column mismatch)
-- =====================================================

DROP VIEW IF EXISTS revenue_by_currency_5min CASCADE;
DROP VIEW IF EXISTS revenue_by_currency_15min CASCADE;
DROP VIEW IF EXISTS revenue_by_currency_30min CASCADE;
DROP VIEW IF EXISTS revenue_by_currency_1hour CASCADE;
DROP VIEW IF EXISTS revenue_by_currency_today CASCADE;
DROP VIEW IF EXISTS revenue_summary_all_windows CASCADE;
DROP VIEW IF EXISTS merchant_performance_5min CASCADE;
DROP VIEW IF EXISTS merchant_performance_15min CASCADE;
DROP VIEW IF EXISTS merchant_performance_30min CASCADE;
DROP VIEW IF EXISTS revenue_by_currency CASCADE;
DROP VIEW IF EXISTS merchant_performance CASCADE;
DROP VIEW IF EXISTS bank_performance CASCADE;
DROP VIEW IF EXISTS mid_bank_performance CASCADE;
DROP VIEW IF EXISTS merchant_timeout CASCADE;
DROP VIEW IF EXISTS timeout_performance CASCADE;
DROP VIEW IF EXISTS overall_statistics CASCADE;

-- =====================================================
-- 1. REVENUE VIEWS (5 time-windowed views)
-- =====================================================

CREATE VIEW revenue_by_currency_5min AS
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

CREATE VIEW revenue_by_currency_15min AS
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

CREATE VIEW revenue_by_currency_30min AS
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

CREATE VIEW revenue_by_currency_1hour AS
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

CREATE VIEW revenue_by_currency_today AS
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

CREATE VIEW revenue_summary_all_windows AS
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
-- NOTE: Includes merchant_name to match existing structure
-- =====================================================

CREATE VIEW merchant_performance_5min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

CREATE VIEW merchant_performance_15min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

CREATE VIEW merchant_performance_30min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- =====================================================
-- 4. ALL-TIME VIEWS (7 views)
-- =====================================================

CREATE VIEW revenue_by_currency AS
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

CREATE VIEW merchant_performance AS
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

CREATE VIEW bank_performance AS
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

CREATE VIEW mid_bank_performance AS
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

CREATE VIEW merchant_timeout AS
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

CREATE VIEW timeout_performance AS
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

CREATE VIEW overall_statistics AS
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

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

GRANT SELECT ON revenue_by_currency_5min TO webhook_user;
GRANT SELECT ON revenue_by_currency_15min TO webhook_user;
GRANT SELECT ON revenue_by_currency_30min TO webhook_user;
GRANT SELECT ON revenue_by_currency_1hour TO webhook_user;
GRANT SELECT ON revenue_by_currency_today TO webhook_user;
GRANT SELECT ON revenue_summary_all_windows TO webhook_user;
GRANT SELECT ON merchant_performance_5min TO webhook_user;
GRANT SELECT ON merchant_performance_15min TO webhook_user;
GRANT SELECT ON merchant_performance_30min TO webhook_user;
GRANT SELECT ON revenue_by_currency TO webhook_user;
GRANT SELECT ON merchant_performance TO webhook_user;
GRANT SELECT ON bank_performance TO webhook_user;
GRANT SELECT ON mid_bank_performance TO webhook_user;
GRANT SELECT ON merchant_timeout TO webhook_user;
GRANT SELECT ON timeout_performance TO webhook_user;
GRANT SELECT ON overall_statistics TO webhook_user;

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

SELECT '=====================================================' as separator;
SELECT '✅ Verification Tests' as test_suite;
SELECT '=====================================================' as separator;

-- Test 1: Check overall_statistics excludes Timesaver
SELECT 'Test 1: Overall Statistics' as test_name,
       total_transactions as total_excluding_timesaver,
       (SELECT COUNT(*) FROM transactions WHERE mid_id = '43110201461') as timesaver_count_not_included
FROM overall_statistics;

-- Test 2: Check revenue views exclude Timesaver
SELECT 'Test 2: Revenue Views (5min)' as test_name,
       SUM(transaction_count) as total_transactions,
       (SELECT COUNT(*) FROM transactions
        WHERE mid_id = '43110201461'
        AND status = 'success'
        AND last_updated_at >= NOW() - INTERVAL '5 minutes') as timesaver_count_not_included
FROM revenue_by_currency_5min;

-- Test 3: Check merchant performance views exclude Timesaver
SELECT 'Test 3: Merchant Performance (5min)' as test_name,
       SUM(total_transactions) as total_excluding_timesaver,
       (SELECT COUNT(*) FROM transactions
        WHERE mid_id = '43110201461'
        AND last_updated_at >= NOW() - INTERVAL '5 minutes') as timesaver_count_not_included
FROM merchant_performance_5min;

SELECT '=====================================================' as separator;
SELECT '✅✅✅ Migration V2 completed successfully!' as final_status;
SELECT 'All 16 views updated with Timesaver exclusions' as details;
SELECT '=====================================================' as separator;
