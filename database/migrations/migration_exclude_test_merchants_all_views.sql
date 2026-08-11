-- Migration: Exclude [TEST] Merchants from All Grafana Views
-- Date: 2025-11-21
-- Description: Update all Grafana views to exclude merchants with [TEST] in their name
-- Impact: Ensures test merchants don't appear in dashboard metrics or monitoring alerts

BEGIN;

-- =====================================================
-- TIMEOUT TRACKING VIEWS - Add merchant_name filter
-- =====================================================

-- Timeout Performance - 5 minutes
CREATE OR REPLACE VIEW timeout_performance_5min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND mid_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- Timeout Performance - 15 minutes
CREATE OR REPLACE VIEW timeout_performance_15min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND mid_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- Timeout Performance - 30 minutes
CREATE OR REPLACE VIEW timeout_performance_30min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND mid_id IS NOT NULL
    -- Exclude test/dummy MIDs
    AND mid_id NOT IN ('43110201461')
    AND (mid_name NOT ILIKE '%timesaver%' OR mid_name IS NULL)
    AND (mid_name NOT ILIKE '%test%' OR mid_name IS NULL)
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

-- =====================================================
-- MERCHANT TIMEOUT VIEWS - Add merchant_name filter
-- =====================================================

-- Merchant Timeout Performance - 5 minutes
CREATE OR REPLACE VIEW merchant_timeout_5min AS
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '5 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') > 0
ORDER BY timeout_rate DESC NULLS LAST;

-- Merchant Timeout Performance - 15 minutes
CREATE OR REPLACE VIEW merchant_timeout_15min AS
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '15 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') > 0
ORDER BY timeout_rate DESC NULLS LAST;

-- Merchant Timeout Performance - 30 minutes
CREATE OR REPLACE VIEW merchant_timeout_30min AS
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '30 minutes'
    AND merchant_id IS NOT NULL
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') > 0
ORDER BY timeout_rate DESC NULLS LAST;

-- =====================================================
-- MERCHANT PERFORMANCE VIEWS - Add merchant_name filter
-- =====================================================

-- Merchant Performance - 5 minutes
CREATE OR REPLACE VIEW merchant_performance_5min AS
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
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- Merchant Performance - 15 minutes
CREATE OR REPLACE VIEW merchant_performance_15min AS
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
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

-- Merchant Performance - 30 minutes
CREATE OR REPLACE VIEW merchant_performance_30min AS
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
    -- Exclude test merchants
    AND (merchant_name NOT ILIKE '%[TEST]%' OR merchant_name IS NULL)
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMIT;

-- Verification
SELECT '✅ All Grafana views updated to exclude [TEST] merchants' as status;

-- Show excluded test merchants
SELECT
    merchant_name,
    COUNT(*) as tx_count_last_24h
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '24 hours'
    AND merchant_name ILIKE '%[TEST]%'
GROUP BY merchant_name
ORDER BY tx_count_last_24h DESC;
