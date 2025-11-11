-- Grafana Dashboard Views
-- Created: 2025-10-28
-- Purpose: Views for Merchant Performance and Timeout Tracking

-- =====================================================
-- MERCHANT PERFORMANCE VIEWS
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
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_5min IS 'Merchant performance for last 5 minutes';

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
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_15min IS 'Merchant performance for last 15 minutes';

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
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_30min IS 'Merchant performance for last 30 minutes';

-- =====================================================
-- TIMEOUT TRACKING VIEWS
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
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW timeout_performance_5min IS 'Timeout tracking for last 5 minutes by MID+Bank';

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
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW timeout_performance_15min IS 'Timeout tracking for last 15 minutes by MID+Bank';

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
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW timeout_performance_30min IS 'Timeout tracking for last 30 minutes by MID+Bank';

-- =====================================================
-- Merchant Timeout Summary
-- =====================================================

CREATE OR REPLACE VIEW merchant_timeout_30min AS
SELECT
    merchant_id,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') as timeout_count,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_desc ILIKE '%timeout%') / NULLIF(COUNT(*), 0), 2) as timeout_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND merchant_id IS NOT NULL
GROUP BY merchant_id
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_timeout_30min IS 'Merchant timeout rates for last 30 minutes';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT ON merchant_performance_5min TO webhook_user;
GRANT SELECT ON merchant_performance_15min TO webhook_user;
GRANT SELECT ON merchant_performance_30min TO webhook_user;
GRANT SELECT ON timeout_performance_5min TO webhook_user;
GRANT SELECT ON timeout_performance_15min TO webhook_user;
GRANT SELECT ON timeout_performance_30min TO webhook_user;
GRANT SELECT ON merchant_timeout_30min TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

SELECT 'Grafana views created successfully!' as status;
