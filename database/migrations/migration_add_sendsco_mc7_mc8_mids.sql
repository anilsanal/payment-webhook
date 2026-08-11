-- Migration: Add Sendsco Mastercard 7 and 8 MID Mappings
-- Date: 2025-11-21
-- Description: Add missing MID mappings for high-volume Sendsco terminals
-- Impact: 26,301 transactions updated (19,266 + 7,035)

BEGIN;

-- Add MID mappings
INSERT INTO mid_mapping (mid_id, terminal_name, notes)
VALUES
    ('4141119152227', 'Sendsco - LIVE - Mastercard 8', 'Added on 2025-11-21 - High volume MID'),
    ('4141118165948', 'Sendsco - LIVE - Mastercard 7', 'Added on 2025-11-21 - High volume MID')
ON CONFLICT (mid_id) DO UPDATE
SET
    terminal_name = EXCLUDED.terminal_name,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

-- Update existing transactions
UPDATE transactions
SET mid_name = 'Sendsco - LIVE - Mastercard 8'
WHERE mid_id = '4141119152227'
  AND (mid_name IS NULL OR mid_name = '');

UPDATE transactions
SET mid_name = 'Sendsco - LIVE - Mastercard 7'
WHERE mid_id = '4141118165948'
  AND (mid_name IS NULL OR mid_name = '');

-- Update webhook_events for audit trail
UPDATE webhook_events
SET mid_name = CASE
    WHEN mid_id = '4141119152227' THEN 'Sendsco - LIVE - Mastercard 8'
    WHEN mid_id = '4141118165948' THEN 'Sendsco - LIVE - Mastercard 7'
END
WHERE mid_id IN ('4141119152227', '4141118165948')
  AND (mid_name IS NULL OR mid_name = '');

COMMIT;

-- Verification queries
SELECT
    mid_id,
    mid_name,
    COUNT(*) as transaction_count
FROM transactions
WHERE mid_id IN ('4141119152227', '4141118165948')
GROUP BY mid_id, mid_name;

SELECT '✅ Migration completed successfully!' as status;
