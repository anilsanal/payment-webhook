-- =====================================================
-- UPDATE GRAFANA VIEWS TO INCLUDE MERCHANT NAMES
-- This fixes the missing merchant names in Grafana dashboards
-- =====================================================

BEGIN;

-- =====================================================
-- MERCHANT PERFORMANCE VIEWS (with merchant_name)
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
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_5min IS 'Merchant performance for last 5 minutes with merchant names';

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
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_15min IS 'Merchant performance for last 15 minutes with merchant names';

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
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_performance_30min IS 'Merchant performance for last 30 minutes with merchant names';

-- =====================================================
-- MERCHANT TIMEOUT VIEWS (with merchant_name)
-- =====================================================

-- Merchant Timeout Performance - 5 minutes
CREATE OR REPLACE VIEW merchant_timeout_5min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND merchant_id IS NOT NULL
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_timeout_5min IS 'Merchant timeout rates for last 5 minutes with merchant names';

-- Merchant Timeout Performance - 15 minutes
CREATE OR REPLACE VIEW merchant_timeout_15min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND merchant_id IS NOT NULL
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_timeout_15min IS 'Merchant timeout rates for last 15 minutes with merchant names';

-- Merchant Timeout Performance - 30 minutes
CREATE OR REPLACE VIEW merchant_timeout_30min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND merchant_id IS NOT NULL
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_timeout_30min IS 'Merchant timeout rates for last 30 minutes with merchant names';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT ON merchant_performance_5min TO webhook_user;
GRANT SELECT ON merchant_performance_15min TO webhook_user;
GRANT SELECT ON merchant_performance_30min TO webhook_user;
GRANT SELECT ON merchant_timeout_5min TO webhook_user;
GRANT SELECT ON merchant_timeout_15min TO webhook_user;
GRANT SELECT ON merchant_timeout_30min TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

-- Show merchants in 30min view
SELECT
    'Updated Views Verification' as check_type,
    merchant_name,
    total_transactions,
    success_rate,
    decline_rate
FROM merchant_performance_30min
ORDER BY total_transactions DESC
LIMIT 10;

COMMIT;

SELECT '✅ Grafana views updated successfully with merchant names!' as final_status;
