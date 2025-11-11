-- =====================================================
-- BANK PERFORMANCE VIEWS (aggregated across all MIDs)
-- These views show success rates by bank only
-- =====================================================

BEGIN;

-- Bank Performance - 5 minutes
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_5min IS 'Bank performance for last 5 minutes (all MIDs aggregated)';

-- Bank Performance - 15 minutes
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_15min IS 'Bank performance for last 15 minutes (all MIDs aggregated)';

-- Bank Performance - 30 minutes
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_30min IS 'Bank performance for last 30 minutes (all MIDs aggregated)';

-- Bank Performance - 1 hour
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_1hour IS 'Bank performance for last 1 hour (all MIDs aggregated)';

-- Bank Performance - 2 hours (baseline for comparison)
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_2hour IS 'Bank performance for last 2 hours (all MIDs aggregated)';

-- Bank Performance - Today
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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance_today IS 'Bank performance for today (all MIDs aggregated)';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT ON bank_performance_5min TO webhook_user;
GRANT SELECT ON bank_performance_15min TO webhook_user;
GRANT SELECT ON bank_performance_30min TO webhook_user;
GRANT SELECT ON bank_performance_1hour TO webhook_user;
GRANT SELECT ON bank_performance_2hour TO webhook_user;
GRANT SELECT ON bank_performance_today TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

-- Show sample data from bank performance view
SELECT
    'Bank Performance 30min' as view_name,
    bank_name,
    total_transactions,
    success_rate,
    decline_rate
FROM bank_performance_30min
ORDER BY total_transactions DESC
LIMIT 10;

COMMIT;

SELECT '✅ Bank performance views created successfully!' as final_status;
