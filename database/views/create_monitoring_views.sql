-- Monitoring System Database Views
-- Created: 2025-10-28
-- Purpose: Track MID + Bank performance for real-time monitoring

-- =====================================================
-- Table: alert_history
-- =====================================================

CREATE TABLE IF NOT EXISTS alert_history (
    id BIGSERIAL PRIMARY KEY,
    alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) NOT NULL,
    time_window VARCHAR(10) NOT NULL,
    mid_id VARCHAR(100),
    mid_name VARCHAR(255),
    bank_name VARCHAR(255),
    total_transactions INTEGER,
    successful INTEGER,
    declined INTEGER,
    pending INTEGER,
    success_rate DECIMAL(5,2),
    decline_rate DECIMAL(5,2),
    message TEXT,
    telegram_message_id INTEGER,
    CONSTRAINT alert_severity_check CHECK (severity IN ('CRITICAL', 'WARNING', 'INFO'))
);

CREATE INDEX IF NOT EXISTS idx_ah_alert_time ON alert_history(alert_time);
CREATE INDEX IF NOT EXISTS idx_ah_mid_bank ON alert_history(mid_id, bank_name);
CREATE INDEX IF NOT EXISTS idx_ah_severity ON alert_history(severity);

COMMENT ON TABLE alert_history IS 'Log of all monitoring alerts sent via Telegram';

-- =====================================================
-- View: mid_bank_performance_5min
-- Real-time performance for last 5 minutes
-- =====================================================

CREATE OR REPLACE VIEW mid_bank_performance_5min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
    AND mid_id IS NOT NULL
    AND bank_name IS NOT NULL
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW mid_bank_performance_5min IS 'MID + Bank performance for last 5 minutes';

-- =====================================================
-- View: mid_bank_performance_15min
-- Performance for last 15 minutes
-- =====================================================

CREATE OR REPLACE VIEW mid_bank_performance_15min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '15 minutes'
    AND mid_id IS NOT NULL
    AND bank_name IS NOT NULL
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW mid_bank_performance_15min IS 'MID + Bank performance for last 15 minutes';

-- =====================================================
-- View: mid_bank_performance_30min
-- Performance for last 30 minutes
-- =====================================================

CREATE OR REPLACE VIEW mid_bank_performance_30min AS
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
WHERE last_updated_at >= NOW() - INTERVAL '30 minutes'
    AND mid_id IS NOT NULL
    AND bank_name IS NOT NULL
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 1
ORDER BY decline_rate DESC NULLS LAST;

COMMENT ON VIEW mid_bank_performance_30min IS 'MID + Bank performance for last 30 minutes';

-- =====================================================
-- View: mid_bank_performance_2hour_baseline
-- Baseline for comparison (2 hour average)
-- =====================================================

CREATE OR REPLACE VIEW mid_bank_performance_2hour_baseline AS
SELECT
    mid_id,
    mid_name,
    bank_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2) as success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'declined') / NULLIF(COUNT(*), 0), 2) as decline_rate
FROM transactions
WHERE last_updated_at >= NOW() - INTERVAL '2 hours'
    AND mid_id IS NOT NULL
    AND bank_name IS NOT NULL
GROUP BY mid_id, mid_name, bank_name
HAVING COUNT(*) >= 10;

COMMENT ON VIEW mid_bank_performance_2hour_baseline IS 'Baseline performance for comparison (2 hour window)';

-- =====================================================
-- View: recent_alerts_summary
-- Summary of recent alerts
-- =====================================================

CREATE OR REPLACE VIEW recent_alerts_summary AS
SELECT
    DATE_TRUNC('hour', alert_time) as hour,
    severity,
    mid_name,
    bank_name,
    COUNT(*) as alert_count,
    AVG(decline_rate) as avg_decline_rate
FROM alert_history
WHERE alert_time >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', alert_time), severity, mid_name, bank_name
ORDER BY hour DESC, alert_count DESC;

COMMENT ON VIEW recent_alerts_summary IS 'Summary of alerts in last 24 hours';

-- =====================================================
-- Grant permissions
-- =====================================================

GRANT SELECT, INSERT ON alert_history TO webhook_user;
GRANT USAGE, SELECT ON SEQUENCE alert_history_id_seq TO webhook_user;
GRANT SELECT ON mid_bank_performance_5min TO webhook_user;
GRANT SELECT ON mid_bank_performance_15min TO webhook_user;
GRANT SELECT ON mid_bank_performance_30min TO webhook_user;
GRANT SELECT ON mid_bank_performance_2hour_baseline TO webhook_user;
GRANT SELECT ON recent_alerts_summary TO webhook_user;

-- =====================================================
-- Verification
-- =====================================================

SELECT 'Monitoring views created successfully!' as status;

-- Show sample data from 30min view
SELECT * FROM mid_bank_performance_30min LIMIT 5;
