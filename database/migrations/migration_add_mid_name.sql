-- Migration Script: Add mid_name field
-- Created: 2025-10-28
-- Purpose: Add mid_name field to store terminal name from mid_mapping

-- =====================================================
-- Add mid_name column to webhook_events table
-- =====================================================

ALTER TABLE webhook_events
ADD COLUMN IF NOT EXISTS mid_name VARCHAR(255);

-- Add index for the new field
CREATE INDEX IF NOT EXISTS idx_we_mid_name ON webhook_events(mid_name);

COMMENT ON COLUMN webhook_events.mid_name IS 'Terminal/Merchant name from mid_mapping table';

-- =====================================================
-- Add mid_name column to transactions table
-- =====================================================

ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS mid_name VARCHAR(255);

-- Add index for the new field
CREATE INDEX IF NOT EXISTS idx_t_mid_name ON transactions(mid_name);

COMMENT ON COLUMN transactions.mid_name IS 'Terminal/Merchant name from mid_mapping table';

-- =====================================================
-- Verification queries
-- =====================================================

-- Verify column was added to webhook_events
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'webhook_events'
    AND column_name = 'mid_name';

-- Verify column was added to transactions
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'transactions'
    AND column_name = 'mid_name';
