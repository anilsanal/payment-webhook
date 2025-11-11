#!/usr/bin/env python3
"""
MidID Mapping Importer
Imports MidID to Terminal Name mappings from CSV to PostgreSQL
"""

import csv
import sys
import psycopg2
from psycopg2.extras import execute_batch
import os

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user': os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD', 'yingyanganil5s'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def import_mid_mappings(csv_file_path):
    """Import MidID mappings from CSV file"""

    print(f"Reading CSV file: {csv_file_path}")

    # Read CSV file
    mappings = []
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Display headers for debugging
        print(f"CSV Headers: {reader.fieldnames}")

        for row in reader:
            # Try to detect column names (case-insensitive)
            mid_id = None
            terminal_name = None

            # Look for MidID column
            for key in row.keys():
                if key.lower() in ['midid', 'mid_id', 'mid id', 'mid', 'terminal id']:
                    mid_id = row[key].strip() if row[key] else None
                elif key.lower() in ['terminal name', 'terminal_name', 'name', 'merchant name', 'merchant_name']:
                    terminal_name = row[key].strip() if row[key] else None

            if mid_id and terminal_name:
                mappings.append((mid_id, terminal_name))
            else:
                print(f"Warning: Skipping row with missing data: {row}")

    print(f"Found {len(mappings)} MidID mappings to import")

    if not mappings:
        print("Error: No valid mappings found in CSV file")
        sys.exit(1)

    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Insert mappings
        print("Inserting MidID mappings...")
        insert_query = """
            INSERT INTO mid_mapping (mid_id, terminal_name)
            VALUES (%s, %s)
            ON CONFLICT (mid_id) DO UPDATE SET
                terminal_name = EXCLUDED.terminal_name,
                updated_at = NOW()
        """

        execute_batch(cursor, insert_query, mappings, page_size=100)

        conn.commit()

        # Display results
        cursor.execute("SELECT COUNT(*) FROM mid_mapping")
        count = cursor.fetchone()[0]
        print(f"\n✓ Successfully imported {count} MidID mappings")

        # Show sample data
        print("\nSample mappings:")
        cursor.execute("SELECT mid_id, terminal_name FROM mid_mapping LIMIT 10")
        for row in cursor.fetchall():
            print(f"  {row[0]:20s} -> {row[1]}")

    except Exception as e:
        conn.rollback()
        print(f"Error importing mappings: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mid_import.py <csv_file_path>")
        print("\nExpected CSV format:")
        print("  - Should have columns for MidID and Terminal Name")
        print("  - Supported column names (case-insensitive):")
        print("    * MidID: 'MidID', 'mid_id', 'mid id', 'mid', 'terminal id'")
        print("    * Name: 'terminal name', 'terminal_name', 'name', 'merchant name', 'merchant_name'")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    import_mid_mappings(csv_file)
