-- Database Schema for Payment Gateway Webhooks
-- Option 3: Hybrid Approach (Audit Trail + Latest Status)

-- =====================================================
-- Table 1: webhook_events (Full Audit Trail)
-- =====================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id BIGSERIAL PRIMARY KEY,
    
    -- Transaction identifiers
    trans_id VARCHAR(100),
    trans_order VARCHAR(100),
    
    -- Status information
    reply_code VARCHAR(10),
    reply_desc TEXT,
    status VARCHAR(20),
    
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
    pm VARCHAR(50),
    cc_bin VARCHAR(10),
    bank_name VARCHAR(255),
    
    -- Additional fields
    plid VARCHAR(100),
    storage_id VARCHAR(100),
    mid_id VARCHAR(100),
    mid_name VARCHAR(255),
    recon_id VARCHAR(100),
    cp26 TEXT,
    cp27 TEXT,
    cp28 TEXT,
    cp29 TEXT,
    cp30 TEXT,

    -- Metadata
    raw_data TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for webhook_events
CREATE INDEX IF NOT EXISTS idx_we_trans_id ON webhook_events(trans_id);
CREATE INDEX IF NOT EXISTS idx_we_trans_order ON webhook_events(trans_order);
CREATE INDEX IF NOT EXISTS idx_we_reply_code ON webhook_events(reply_code);
CREATE INDEX IF NOT EXISTS idx_we_status ON webhook_events(status);
CREATE INDEX IF NOT EXISTS idx_we_received_at ON webhook_events(received_at);
CREATE INDEX IF NOT EXISTS idx_we_cc_bin ON webhook_events(cc_bin);
CREATE INDEX IF NOT EXISTS idx_we_bank_name ON webhook_events(bank_name);
CREATE INDEX IF NOT EXISTS idx_we_client_country ON webhook_events(client_country);
CREATE INDEX IF NOT EXISTS idx_we_mid_id ON webhook_events(mid_id);
CREATE INDEX IF NOT EXISTS idx_we_mid_name ON webhook_events(mid_name);
CREATE INDEX IF NOT EXISTS idx_we_recon_id ON webhook_events(recon_id);

-- =====================================================
-- Table 2: transactions (Latest Status per Transaction)
-- =====================================================

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    
    -- Transaction identifiers
    trans_id VARCHAR(100) UNIQUE NOT NULL,
    trans_order VARCHAR(100),
    
    -- Current status information
    reply_code VARCHAR(10),
    reply_desc TEXT,
    status VARCHAR(20),
    
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
    bank_name VARCHAR(255),

    -- Additional fields
    mid_id VARCHAR(100),
    mid_name VARCHAR(255),
    recon_id VARCHAR(100),

    -- Metadata
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for transactions
CREATE INDEX IF NOT EXISTS idx_t_status_updated ON transactions(status, last_updated_at);
CREATE INDEX IF NOT EXISTS idx_t_trans_date ON transactions(trans_date);
CREATE INDEX IF NOT EXISTS idx_t_cc_bin_status ON transactions(cc_bin, status);
CREATE INDEX IF NOT EXISTS idx_t_bank_name_status ON transactions(bank_name, status);
CREATE INDEX IF NOT EXISTS idx_t_country_status ON transactions(client_country, status);
CREATE INDEX IF NOT EXISTS idx_t_mid_id ON transactions(mid_id);
CREATE INDEX IF NOT EXISTS idx_t_mid_name ON transactions(mid_name);
CREATE INDEX IF NOT EXISTS idx_t_recon_id ON transactions(recon_id);

-- =====================================================
-- Table 3: mid_mapping (MidID to Terminal Name)
-- =====================================================

CREATE TABLE IF NOT EXISTS mid_mapping (
    id SERIAL PRIMARY KEY,
    mid_id VARCHAR(100) UNIQUE NOT NULL,
    terminal_name VARCHAR(255) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for mid_mapping
CREATE INDEX IF NOT EXISTS idx_mid_id_lookup ON mid_mapping(mid_id);
CREATE INDEX IF NOT EXISTS idx_terminal_name_lookup ON mid_mapping(terminal_name);

-- =====================================================
-- Table 4: bin_bank_mapping
-- =====================================================

CREATE TABLE IF NOT EXISTS bin_bank_mapping (
    id SERIAL PRIMARY KEY,
    bin VARCHAR(10) UNIQUE NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    bank_country VARCHAR(10),
    card_type VARCHAR(50),
    card_brand VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for bin_bank_mapping
CREATE INDEX IF NOT EXISTS idx_bin_lookup ON bin_bank_mapping(bin);
CREATE INDEX IF NOT EXISTS idx_bank_name_lookup ON bin_bank_mapping(bank_name);

-- =====================================================
-- Views for Metabase Dashboards
-- =====================================================

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
-- Grant permissions
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhook_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhook_user;

-- Sample BIN mapping
INSERT INTO bin_bank_mapping (bin, bank_name, bank_country, card_type, card_brand) 
VALUES ('540709', 'Unknown Bank', 'TR', 'CREDIT', 'MASTERCARD')
ON CONFLICT (bin) DO NOTHING;
