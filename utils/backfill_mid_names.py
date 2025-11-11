#!/usr/bin/env python3
"""
Backfill MidID Names Script
Updates existing webhook_events and transactions records with mid_name from mid_mapping table
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user': os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD', 'yingyanganil5s'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def backfill_mid_names():
    """Backfill mid_name for existing records"""

    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Step 1: Update webhook_events table
        print("\n=== Updating webhook_events table ===")

        # Count records that need updating
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM webhook_events we
            WHERE we.mid_id IS NOT NULL
              AND we.mid_name IS NULL
              AND EXISTS (SELECT 1 FROM mid_mapping mm WHERE mm.mid_id = we.mid_id)
        """)
        count = cursor.fetchone()['count']
        print(f"Found {count} webhook_events records to update")

        if count > 0:
            # Update records
            cursor.execute("""
                UPDATE webhook_events we
                SET mid_name = mm.terminal_name
                FROM mid_mapping mm
                WHERE we.mid_id = mm.mid_id
                  AND we.mid_name IS NULL
            """)
            print(f"✓ Updated {cursor.rowcount} webhook_events records")

        # Step 2: Update transactions table
        print("\n=== Updating transactions table ===")

        # Count records that need updating
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM transactions t
            WHERE t.mid_id IS NOT NULL
              AND t.mid_name IS NULL
              AND EXISTS (SELECT 1 FROM mid_mapping mm WHERE mm.mid_id = t.mid_id)
        """)
        count = cursor.fetchone()['count']
        print(f"Found {count} transactions records to update")

        if count > 0:
            # Update records
            cursor.execute("""
                UPDATE transactions t
                SET mid_name = mm.terminal_name
                FROM mid_mapping mm
                WHERE t.mid_id = mm.mid_id
                  AND t.mid_name IS NULL
            """)
            print(f"✓ Updated {cursor.rowcount} transactions records")

        conn.commit()

        # Step 3: Show statistics
        print("\n=== Statistics ===")

        # webhook_events stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(mid_id) as with_mid_id,
                COUNT(mid_name) as with_mid_name,
                COUNT(*) FILTER (WHERE mid_id IS NOT NULL AND mid_name IS NULL) as missing_mid_name
            FROM webhook_events
        """)
        stats = cursor.fetchone()
        print(f"\nwebhook_events:")
        print(f"  Total records: {stats['total']}")
        print(f"  With mid_id: {stats['with_mid_id']}")
        print(f"  With mid_name: {stats['with_mid_name']}")
        print(f"  Missing mid_name (have mid_id): {stats['missing_mid_name']}")

        # transactions stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(mid_id) as with_mid_id,
                COUNT(mid_name) as with_mid_name,
                COUNT(*) FILTER (WHERE mid_id IS NOT NULL AND mid_name IS NULL) as missing_mid_name
            FROM transactions
        """)
        stats = cursor.fetchone()
        print(f"\ntransactions:")
        print(f"  Total records: {stats['total']}")
        print(f"  With mid_id: {stats['with_mid_id']}")
        print(f"  With mid_name: {stats['with_mid_name']}")
        print(f"  Missing mid_name (have mid_id): {stats['missing_mid_name']}")

        # Show sample of unmapped MidIDs
        print("\n=== Unmapped MidIDs (top 10) ===")
        cursor.execute("""
            SELECT DISTINCT mid_id, COUNT(*) as count
            FROM transactions
            WHERE mid_id IS NOT NULL
              AND mid_name IS NULL
            GROUP BY mid_id
            ORDER BY count DESC
            LIMIT 10
        """)
        unmapped = cursor.fetchall()
        if unmapped:
            print("These MidIDs exist in transactions but not in mid_mapping:")
            for row in unmapped:
                print(f"  {row['mid_id']:20s} ({row['count']} records)")
        else:
            print("No unmapped MidIDs found!")

        print("\n✓ Backfill completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error during backfill: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MidID Names Backfill Script")
    print("=" * 60)

    backfill_mid_names()
