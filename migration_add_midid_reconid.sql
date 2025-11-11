-- Migration Script: Add MidID and ReconID fields
-- Created: 2025-10-28
-- Purpose: Support new webhook structure with MidID and ReconID fields

-- =====================================================
-- Add new columns to webhook_events table
-- =====================================================

ALTER TABLE webhook_events
ADD COLUMN IF NOT EXISTS mid_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS recon_id VARCHAR(100);

-- Add indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_we_mid_id ON webhook_events(mid_id);
CREATE INDEX IF NOT EXISTS idx_we_recon_id ON webhook_events(recon_id);

COMMENT ON COLUMN webhook_events.mid_id IS 'Merchant Integration ID from payment gateway';
COMMENT ON COLUMN webhook_events.recon_id IS 'Reconciliation ID from payment gateway';

-- =====================================================
-- Add new columns to transactions table
-- =====================================================

ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS mid_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS recon_id VARCHAR(100);

-- Add indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_t_mid_id ON transactions(mid_id);
CREATE INDEX IF NOT EXISTS idx_t_recon_id ON transactions(recon_id);

COMMENT ON COLUMN transactions.mid_id IS 'Merchant Integration ID from payment gateway';
COMMENT ON COLUMN transactions.recon_id IS 'Reconciliation ID from payment gateway';

-- =====================================================
-- Verification queries
-- =====================================================

-- Verify columns were added to webhook_events
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'webhook_events'
    AND column_name IN ('mid_id', 'recon_id');

-- Verify columns were added to transactions
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'transactions'
    AND column_name IN ('mid_id', 'recon_id');

-- Check indexes
SELECT
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE tablename IN ('webhook_events', 'transactions')
    AND indexname LIKE '%mid_id%' OR indexname LIKE '%recon_id%';
