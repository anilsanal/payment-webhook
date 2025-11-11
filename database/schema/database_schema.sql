-- Database Schema for Payment Gateway Webhooks
-- Option 3: Hybrid Approach (Audit Trail + Latest Status)

-- =====================================================
-- Table 1: webhook_events (Full Audit Trail)
-- Every webhook received is stored here
-- =====================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id BIGSERIAL PRIMARY KEY,
    
    -- Transaction identifiers
    trans_id VARCHAR(100),
    trans_order VARCHAR(100),
    
    -- Status information
    reply_code VARCHAR(10),
    reply_desc TEXT,
    status VARCHAR(20), -- 'pending', 'success', 'declined'
    
    -- Transaction details
    trans_date VARCHAR(100),
    otrans_amount DECIMAL(15, 4), -- Original amount
    trans_amount DECIMAL(15, 4),  -- Converted amount
    otrans_currency VARCHAR(10),
    trans_currency VARCHAR(10),
    
    -- Merchant information
    merchant_id VARCHAR(50),
    
    -- Customer information
    client_fullname VARCHAR(255),
    client_phone VARCHAR(50),
    client_email VARCHAR(255),
    
    -- Payment information
    payment_details TEXT,
    exp_month VARCHAR(2),
    exp_year VARCHAR(4),
    trans_type VARCHAR(10),
    
    -- Security
    signature TEXT,
    
    -- System references
    system_reference VARCHAR(100),
    debit_company VARCHAR(50),
    debrefnum VARCHAR(100),
    debrefcode VARCHAR(100),
    debit_companyname VARCHAR(255),
    
    -- Transaction flags
    is3d VARCHAR(10),
    is_refund VARCHAR(10),
    
    -- Customer address
    client_address TEXT,
    client_address2 TEXT,
    client_zipcode VARCHAR(20),
    client_country VARCHAR(10),
    client_city VARCHAR(100),
    
    -- Card information
    bin_country VARCHAR(10),
    pm VARCHAR(50), -- Payment method
    cc_bin VARCHAR(10), -- Card BIN (first 6 digits)
    bank_name VARCHAR(255), -- Resolved from BIN mapping
    
    -- Additional fields
    plid VARCHAR(100),
    storage_id VARCHAR(100),
    cp26 TEXT,
    cp27 TEXT,
    cp28 TEXT,
    cp29 TEXT,
    cp30 TEXT,
    
    -- Metadata
    raw_data TEXT, -- Store full raw webhook data for debugging
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for fast queries
    INDEX idx_trans_id (trans_id),
    INDEX idx_trans_order (trans_order),
    INDEX idx_reply_code (reply_code),
    INDEX idx_status (status),
    INDEX idx_received_at (received_at),
    INDEX idx_cc_bin (cc_bin),
    INDEX idx_bank_name (bank_name),
    INDEX idx_client_country (client_country)
);

-- =====================================================
-- Table 2: transactions (Latest Status per Transaction)
-- Only current status for each unique trans_id
-- =====================================================

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    
    -- Transaction identifiers (trans_id is unique)
    trans_id VARCHAR(100) UNIQUE NOT NULL,
    trans_order VARCHAR(100),
    
    -- Current status information
    reply_code VARCHAR(10),
    reply_desc TEXT,
    status VARCHAR(20), -- 'pending', 'success', 'declined'
    
    -- Transaction details
    trans_date VARCHAR(100),
    otrans_amount DECIMAL(15, 4),
    trans_amount DECIMAL(15, 4),
    otrans_currency VARCHAR(10),
    trans_currency VARCHAR(10),
    
    -- Merchant information
    merchant_id VARCHAR(50),
    
    -- Customer information
    client_fullname VARCHAR(255),
    client_phone VARCHAR(50),
    client_email VARCHAR(255),
    
    -- Payment information
    payment_details TEXT,
    exp_month VARCHAR(2),
    exp_year VARCHAR(4),
    trans_type VARCHAR(10),
    
    -- System references
    system_reference VARCHAR(100),
    debit_company VARCHAR(50),
    debrefnum VARCHAR(100),
    debrefcode VARCHAR(100),
    debit_companyname VARCHAR(255),
    
    -- Transaction flags
    is3d VARCHAR(10),
    is_refund VARCHAR(10),
    
    -- Customer address
    client_address TEXT,
    client_address2 TEXT,
    client_zipcode VARCHAR(20),
    client_country VARCHAR(10),
    client_city VARCHAR(100),
    
    -- Card information
    bin_country VARCHAR(10),
    pm VARCHAR(50),
    cc_bin VARCHAR(10),
    bank_name VARCHAR(255), -- Resolved from BIN mapping
    
    -- Metadata
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for dashboard queries
    INDEX idx_status_updated (status, last_updated_at),
    INDEX idx_trans_date (trans_date),
    INDEX idx_cc_bin_status (cc_bin, status),
    INDEX idx_bank_name_status (bank_name, status),
    INDEX idx_country_status (client_country, status)
);

-- =====================================================
-- Table 3: bin_bank_mapping (BIN to Bank Name Mapping)
-- You'll populate this with your BIN list
-- =====================================================

CREATE TABLE IF NOT EXISTS bin_bank_mapping (
    id SERIAL PRIMARY KEY,
    bin VARCHAR(10) UNIQUE NOT NULL, -- 6-digit BIN
    bank_name VARCHAR(255) NOT NULL,
    bank_country VARCHAR(10),
    card_type VARCHAR(50), -- 'CREDIT', 'DEBIT', 'PREPAID'
    card_brand VARCHAR(50), -- 'VISA', 'MASTERCARD', 'AMEX', etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_bin_lookup (bin),
    INDEX idx_bank_name_lookup (bank_name)
);

-- =====================================================
-- Useful Views for Metabase Dashboards
-- =====================================================

-- View: Current day transactions summary
CREATE OR REPLACE VIEW daily_transactions_summary AS
SELECT 
    DATE(last_updated_at) as transaction_date,
    status,
    COUNT(*) as transaction_count,
    SUM(trans_amount::numeric) as total_amount,
    trans_currency,
    ROUND(AVG(trans_amount::numeric), 2) as avg_amount
FROM transactions
WHERE last_updated_at >= CURRENT_DATE
GROUP BY DATE(last_updated_at), status, trans_currency;

-- View: BIN analysis with bank names
CREATE OR REPLACE VIEW bin_analysis AS
SELECT 
    t.cc_bin,
    t.bank_name,
    t.status,
    COUNT(*) as transaction_count,
    SUM(t.trans_amount::numeric) as total_amount,
    ROUND(AVG(t.trans_amount::numeric), 2) as avg_amount,
    t.trans_currency
FROM transactions t
WHERE t.cc_bin IS NOT NULL
GROUP BY t.cc_bin, t.bank_name, t.status, t.trans_currency;

-- View: Hourly success rate
CREATE OR REPLACE VIEW hourly_success_rate AS
SELECT 
    DATE_TRUNC('hour', last_updated_at) as hour,
    COUNT(*) FILTER (WHERE status = 'success') as successful,
    COUNT(*) FILTER (WHERE status = 'declined') as declined,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) as total,
    ROUND(
        (COUNT(*) FILTER (WHERE status = 'success')::numeric / 
         NULLIF(COUNT(*) FILTER (WHERE status IN ('success', 'declined')), 0) * 100), 
        2
    ) as success_rate_percentage
FROM transactions
WHERE last_updated_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', last_updated_at)
ORDER BY hour DESC;

-- =====================================================
-- Grant permissions to webhook_user
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhook_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhook_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO webhook_user;

-- =====================================================
-- Sample data for testing (optional)
-- =====================================================

-- Insert some sample BIN mappings
-- You'll replace this with your actual BIN list

INSERT INTO bin_bank_mapping (bin, bank_name, bank_country, card_type, card_brand) 
VALUES 
    ('540709', 'Unknown Bank', 'TR', 'CREDIT', 'MASTERCARD')
ON CONFLICT (bin) DO NOTHING;

-- Note: After running this schema, you should populate bin_bank_mapping 
-- with your complete BIN to Bank Name list
