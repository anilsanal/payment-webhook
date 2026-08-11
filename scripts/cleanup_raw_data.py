#!/usr/bin/env python3
"""
Nightly cleanup: null out raw_data on webhook_events older than RETENTION_DAYS.
Commits every BATCH_SIZE rows so it's safe to kill and restart at any point.
"""

import psycopg2
import time
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv('/opt/payment-webhook/.env')

BATCH_SIZE = 1000
SLEEP_BETWEEN_BATCHES = 0.05   # seconds — keeps I/O pressure low
RETENTION_DAYS = 60

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s cleanup_raw_data %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/opt/payment-webhook/logs/cleanup_raw_data.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user':   os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD'),
    'host':   os.getenv('DB_HOST', 'localhost'),
    'port':   os.getenv('DB_PORT', '5432'),
}

def run():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    total = 0

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT count(*) FROM webhook_events
                WHERE raw_data IS NOT NULL
                  AND received_at < NOW() - INTERVAL '%s days'
            """, (RETENTION_DAYS,))
            pending = cur.fetchone()[0]

        if pending == 0:
            log.info("Nothing to clean up.")
            return

        log.info(f"Starting cleanup: {pending:,} rows to null (>{RETENTION_DAYS} days old)")

        while True:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE webhook_events
                    SET raw_data = NULL
                    WHERE id IN (
                        SELECT id FROM webhook_events
                        WHERE raw_data IS NOT NULL
                          AND received_at < NOW() - INTERVAL '%s days'
                        ORDER BY received_at
                        LIMIT %s
                    )
                """, (RETENTION_DAYS, BATCH_SIZE))
                rows = cur.rowcount

            conn.commit()

            if rows == 0:
                break

            total += rows
            time.sleep(SLEEP_BETWEEN_BATCHES)

        log.info(f"Done. Nulled {total:,} rows total.")

    except Exception as e:
        conn.rollback()
        log.error(f"Failed after {total:,} rows: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    run()
