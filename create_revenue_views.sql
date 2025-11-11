-- =====================================================
-- REVENUE VIEWS BY CURRENCY
-- These views show total revenue from successful transactions
-- grouped by currency for different time windows
-- =====================================================

BEGIN;

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency_5min IS 'Total revenue by currency for last 5 minutes (successful transactions only)';

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency_15min IS 'Total revenue by currency for last 15 minutes (successful transactions only)';

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency_30min IS 'Total revenue by currency for last 30 minutes (successful transactions only)';

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency_1hour IS 'Total revenue by currency for last 1 hour (successful transactions only)';

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
GROUP BY trans_currency
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_currency_today IS 'Total revenue by currency for today (successful transactions only)';

-- =====================================================
-- COMBINED REVENUE VIEW (All time windows in one query)
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
GROUP BY trans_currency

ORDER BY time_window, total_revenue DESC;

COMMENT ON VIEW revenue_summary_all_windows IS 'Revenue summary across multiple time windows for comparison';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT ON revenue_by_currency_5min TO webhook_user;
GRANT SELECT ON revenue_by_currency_15min TO webhook_user;
GRANT SELECT ON revenue_by_currency_30min TO webhook_user;
GRANT SELECT ON revenue_by_currency_1hour TO webhook_user;
GRANT SELECT ON revenue_by_currency_today TO webhook_user;
GRANT SELECT ON revenue_summary_all_windows TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

-- Show current revenue data
SELECT
    'Revenue Today' as report,
    currency,
    transaction_count,
    TO_CHAR(total_revenue, 'FM999,999,999.00') as formatted_revenue,
    TO_CHAR(avg_transaction_amount, 'FM999,999.00') as avg_amount
FROM revenue_by_currency_today
ORDER BY total_revenue DESC;

COMMIT;

SELECT '✅ Revenue views created successfully!' as final_status;
