-- Migration: Exclude 503 Reply Code from Success Rate Calculations
-- Date: 2025-11-21
-- Description: Update all success rate calculations to exclude reply_code 503 errors
-- Reason: 503 errors ("Merchant unauthorized to process this type of payment method
--         in this currency or this country") are merchant configuration issues,
--         not actual transaction failures that should impact success rate metrics
-- Impact: More accurate success rate reporting, especially for Panelix merchant

-- =====================================================
-- ANALYSIS OF 503 ERRORS
-- =====================================================

-- Total 503 errors in system
-- All time: 1,323 transactions
-- Last 24 hours: 1,138 transactions (2.5% of all transactions)
-- Last 7 days: 1,183 transactions

-- Primary affected merchant: Panelix [LIVE]
-- Panelix 503 count: 1,140 transactions (86% of all 503 errors)
-- Started: Nov 19, 2025 (recent issue - likely configuration change)
-- Pattern: TRY currency + Turkey country (99.9% of 503 errors)

-- Impact on Panelix success rate (last 12 hours):
-- With 503 included: 38.84%
-- Without 503 excluded: 46.53%
-- Improvement: +7.69 percentage points

-- =====================================================
-- DASHBOARD UPDATES
-- =====================================================

-- All Grafana dashboard panels have been updated with the following changes:

-- OLD FORMULA:
-- ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2)

-- NEW FORMULA:
-- ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') /
--       NULLIF(COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503'), 0), 2)

-- PANELS UPDATED:
-- 1. Success Rate (top stat)
-- 2. Timeout Rate (denominator adjusted)
-- 3. MID + Bank Performance (success_rate and decline_rate columns)
-- 4. Success Rate by Merchant
-- 5. Timeout Rate by Merchant (denominator adjusted)
-- 6. Success Rate by Merchant (Purged) - added '503' to exclusion list

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Overall impact (last 12 hours)
SELECT
    'Overall Impact' as metric,
    COUNT(*) as total_with_503,
    COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503') as total_without_503,
    COUNT(*) FILTER (WHERE reply_code = '503') as excluded_503,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as old_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503'), 0), 2) as new_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503'), 0), 2) -
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as improvement
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '12 hours'
    AND (mid_id IS NULL OR mid_id NOT IN ('43110201461'))
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%timesaver%')
    AND (mid_name IS NULL OR mid_name NOT ILIKE '%test%')
    AND (merchant_name IS NULL OR merchant_name NOT ILIKE '%[TEST]%');

-- Panelix specific impact
SELECT
    'Panelix Impact' as metric,
    COUNT(*) as total_with_503,
    COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503') as total_without_503,
    COUNT(*) FILTER (WHERE reply_code = '503') as excluded_503,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as old_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503'), 0), 2) as new_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*) FILTER (WHERE reply_code IS NULL OR reply_code != '503'), 0), 2) -
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as improvement
FROM transactions
WHERE trans_datetime >= NOW() - INTERVAL '12 hours'
    AND merchant_name = 'Panelix [LIVE]';

-- 503 error breakdown by merchant
SELECT
    merchant_name,
    COUNT(*) FILTER (WHERE reply_code = '503') as count_503,
    COUNT(*) FILTER (WHERE trans_datetime >= NOW() - INTERVAL '24 hours' AND reply_code = '503') as last_24h_503,
    MIN(trans_datetime) FILTER (WHERE reply_code = '503') as first_503_error,
    MAX(trans_datetime) FILTER (WHERE reply_code = '503') as last_503_error
FROM transactions
WHERE reply_code = '503'
GROUP BY merchant_name
ORDER BY count_503 DESC;

SELECT '✅ Migration documentation complete - dashboard has been updated' as status;
