-- Create MidID Mapping Table
-- Created: 2025-10-28
-- Purpose: Store MidID to Terminal Name mappings

-- =====================================================
-- Table: mid_mapping
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

COMMENT ON TABLE mid_mapping IS 'Mapping of MidID to Terminal Names for transaction enrichment';
COMMENT ON COLUMN mid_mapping.mid_id IS 'Merchant Integration ID from payment gateway';
COMMENT ON COLUMN mid_mapping.terminal_name IS 'Human-readable terminal/merchant name';

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE mid_mapping TO webhook_user;
GRANT ALL PRIVILEGES ON SEQUENCE mid_mapping_id_seq TO webhook_user;

-- Verification query
SELECT
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'mid_mapping'
ORDER BY ordinal_position;
