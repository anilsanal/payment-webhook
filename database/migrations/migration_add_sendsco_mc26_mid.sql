-- Migration: Add Sendsco Mastercard 26 MID Mapping
-- Date: 2026-06-22
-- Description: Add missing MID mapping for mid_id 414622153451
-- Impact: 30 existing transactions/webhook_events backfilled

BEGIN;

-- Add MID mapping (also drives mid_name for all future transactions via mid_mapping cache)
INSERT INTO mid_mapping (mid_id, terminal_name, notes)
VALUES
    ('414622153451', 'Sendsco - LIVE - Mastercard 26', 'Added on 2026-06-22')
ON CONFLICT (mid_id) DO UPDATE
SET
    terminal_name = EXCLUDED.terminal_name,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

-- Update existing transactions
UPDATE transactions
SET mid_name = 'Sendsco - LIVE - Mastercard 26'
WHERE mid_id = '414622153451';

-- Update webhook_events for audit trail
UPDATE webhook_events
SET mid_name = 'Sendsco - LIVE - Mastercard 26'
WHERE mid_id = '414622153451';

COMMIT;

-- Verification queries
SELECT
    mid_id,
    mid_name,
    COUNT(*) as transaction_count
FROM transactions
WHERE mid_id = '414622153451'
GROUP BY mid_id, mid_name;

SELECT '✅ Migration completed successfully!' as status;
