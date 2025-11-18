-- =====================================================
-- Migration: Exclude Test/Dummy MIDs from ALL Grafana & Monitoring Views
-- Created: 2025-11-18
-- Purpose: Update ALL views to exclude test MIDs like '43110201461' and 'Timesaver'
-- =====================================================

BEGIN;

-- Define the exclusion filter as a comment for reference
-- EXCLUSION FILTER:
--   AND mid_id NOT IN ('43110201461')
--   AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
--   AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)

-- =====================================================
-- 1. MONITORING VIEWS (mid_bank_performance_*)
-- =====================================================

CREATE OR REPLACE VIEW mid_bank_performance_5min AS
SELECT
    mid_id, mid_name, bank_name,
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
    AND mid_id IS NOT NULL AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

CREATE OR REPLACE VIEW mid_bank_performance_15min AS
SELECT
    mid_id, mid_name, bank_name,
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
    AND mid_id IS NOT NULL AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

CREATE OR REPLACE VIEW mid_bank_performance_30min AS
SELECT
    mid_id, mid_name, bank_name,
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
    AND mid_id IS NOT NULL AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

CREATE OR REPLACE VIEW mid_bank_performance_2hour_baseline AS
SELECT
    mid_id, mid_name, bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '2 hours'
    AND mid_id IS NOT NULL AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 10;

-- =====================================================
-- 2. TIMEOUT PERFORMANCE VIEWS (timeout_performance_*)
-- =====================================================

CREATE OR REPLACE VIEW timeout_performance_5min AS
SELECT
    mid_id, mid_name, bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND mid_id IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

CREATE OR REPLACE VIEW timeout_performance_15min AS
SELECT
    mid_id, mid_name, bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND mid_id IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

CREATE OR REPLACE VIEW timeout_performance_30min AS
SELECT
    mid_id, mid_name, bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    MIN(last_updated_at) as first_transaction,
    MAX(last_updated_at) as last_transaction
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND mid_id IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- =====================================================
-- 3. BANK PERFORMANCE VIEWS (bank_performance_*)
-- These aggregate across all MIDs, so exclude test MIDs
-- =====================================================

CREATE OR REPLACE VIEW bank_performance_5min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

CREATE OR REPLACE VIEW bank_performance_15min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

CREATE OR REPLACE VIEW bank_performance_30min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

CREATE OR REPLACE VIEW bank_performance_1hour AS
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
WHERE last_updated_at >= NOW() - INTERVAL '1 hour'
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

CREATE OR REPLACE VIEW bank_performance_2hour AS
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
WHERE last_updated_at >= NOW() - INTERVAL '2 hours'
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

CREATE OR REPLACE VIEW bank_performance_today AS
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
WHERE DATE(last_updated_at) = CURRENT_DATE
    AND bank_name IS NOT NULL
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

-- =====================================================
-- 4. REVENUE VIEWS (revenue_by_currency_*)
-- Exclude test MID transactions from revenue calculations
-- =====================================================

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
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY trans_currency
ORDER BY total_revenue DESC;

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
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY trans_currency
ORDER BY total_revenue DESC;

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
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY trans_currency
ORDER BY total_revenue DESC;

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
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY trans_currency
ORDER BY total_revenue DESC;

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
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMIT;

-- =====================================================
-- Verification
-- =====================================================

SELECT '✅ Migration completed: Test MIDs excluded from ALL views' as status;

-- Show count of excluded transactions
SELECT
    'Excluded Test MID Transactions' as check_type,
    COUNT(*) as count
FROM transactions
WHERE mid_id IN ('43110201461')
    OR mid_name ILIKE '%timesaver%'
    OR mid_name ILIKE '%test%';

-- Verify a sample view
SELECT 'Sample check: timeout_performance_5min' as view_check;
SELECT mid_id, mid_name, bank_name, total_transactions
FROM timeout_performance_5min
LIMIT 5;
