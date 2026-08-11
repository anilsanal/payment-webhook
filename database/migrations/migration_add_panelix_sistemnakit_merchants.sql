-- Migration: Add Panelix and Sistemnakit Merchant Mappings
-- Date: 2025-11-21
-- Description: Add missing merchant mappings for high-volume merchants
-- Impact: 6,177 transactions updated (6,051 Panelix + 126 Sistemnakit)

BEGIN;

-- Add merchant mappings
INSERT INTO merchant_mapping (merchant_id, merchant_name)
VALUES
    ('1885994', 'Panelix [LIVE]'),
    ('4362197', 'Sistemnakit [TEST]')
ON CONFLICT (merchant_id) DO UPDATE
SET merchant_name = EXCLUDED.merchant_name;

-- Update existing transactions
UPDATE transactions
SET merchant_name = 'Panelix [LIVE]'
WHERE merchant_id = '1885994'
  AND (merchant_name IS NULL OR merchant_name = '');

UPDATE transactions
SET merchant_name = 'Sistemnakit [TEST]'
WHERE merchant_id = '4362197'
  AND (merchant_name IS NULL OR merchant_name = '');

-- Update webhook_events for audit trail
UPDATE webhook_events
SET merchant_name = CASE
    WHEN merchant_id = '1885994' THEN 'Panelix [LIVE]'
    WHEN merchant_id = '4362197' THEN 'Sistemnakit [TEST]'
END
WHERE merchant_id IN ('1885994', '4362197')
  AND (merchant_name IS NULL OR merchant_name = '');

COMMIT;

-- Verification queries
SELECT
    merchant_id,
    merchant_name,
    COUNT(*) as transaction_count
FROM transactions
WHERE merchant_id IN ('1885994', '4362197')
GROUP BY merchant_id, merchant_name;

SELECT '✅ Migration completed successfully!' as status;
