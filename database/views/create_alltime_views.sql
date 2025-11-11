-- =====================================================
-- ALL-TIME VIEWS (No Time Filters)
-- These views show all historical data
-- =====================================================

BEGIN;

-- =====================================================
-- REVENUE BY CURRENCY (All Time)
-- =====================================================

DROP VIEW IF EXISTS revenue_by_currency CASCADE;

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency IS 'Total revenue by currency (all time, successful transactions only)';

-- =====================================================
-- MERCHANT PERFORMANCE (All Time)
-- =====================================================

DROP VIEW IF EXISTS merchant_performance CASCADE;

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
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW merchant_performance IS 'Merchant performance (all time)';

-- =====================================================
-- BANK PERFORMANCE (All Time)
-- =====================================================

DROP VIEW IF EXISTS bank_performance CASCADE;

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
GROUP BY bank_name
HAVING COUNT(*) >= 1
ORDER BY total_transactions DESC;

COMMENT ON VIEW bank_performance IS 'Bank performance (all time, all MIDs aggregated)';

-- =====================================================
-- MID + BANK PERFORMANCE (All Time)
-- =====================================================

DROP VIEW IF EXISTS mid_bank_performance CASCADE;

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
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW mid_bank_performance IS 'MID + Bank performance (all time)';

-- =====================================================
-- MERCHANT TIMEOUT PERFORMANCE (All Time)
-- =====================================================

DROP VIEW IF EXISTS merchant_timeout CASCADE;

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
GROUP BY merchant_id, merchant_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW merchant_timeout IS 'Merchant timeout rates (all time)';

-- =====================================================
-- TIMEOUT PERFORMANCE BY MID+BANK (All Time)
-- =====================================================

DROP VIEW IF EXISTS timeout_performance CASCADE;

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
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY timeout_rate DESC NULLS LAST;

COMMENT ON VIEW timeout_performance IS 'Timeout tracking (all time) by MID+Bank';

-- =====================================================
-- OVERALL STATISTICS (All Time Summary)
-- =====================================================

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
FROM transactions;

COMMENT ON VIEW overall_statistics IS 'Overall system statistics (all time)';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT ON revenue_by_currency TO webhook_user;
GRANT SELECT ON merchant_performance TO webhook_user;
GRANT SELECT ON bank_performance TO webhook_user;
GRANT SELECT ON mid_bank_performance TO webhook_user;
GRANT SELECT ON merchant_timeout TO webhook_user;
GRANT SELECT ON timeout_performance TO webhook_user;
GRANT SELECT ON overall_statistics TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

SELECT 'All-Time Views Summary' as report_type;

-- Revenue Summary
SELECT
    'Revenue (All Time)' as metric,
    currency,
    transaction_count,
    ROUND(total_revenue, 2) as total_revenue
FROM revenue_by_currency
ORDER BY total_revenue DESC;

-- Overall Stats
SELECT
    'Overall Statistics' as report,
    total_transactions,
    overall_success_rate,
    overall_decline_rate,
    total_merchants,
    total_banks
FROM overall_statistics;

COMMIT;

SELECT '✅ All-time views created successfully!' as final_status;
