#!/usr/bin/env python3
import csv
import psycopg2

DB_CONFIG = {
    'dbname': 'payment_transactions',
    'user': 'webhook_user',
    'password': 'yingyanganil5s',
    'host': 'localhost',
    'port': '5432'
}

print("Connecting to database...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    # Step 1: Clear all existing data
    print("Clearing existing merchant mapping data...")
    cursor.execute("TRUNCATE merchant_mapping CASCADE;")
    conn.commit()
    print("✓ Cleared")
    
    # Step 2: Import from CSV
    print("Reading CSV file...")
    with open('/opt/payment-webhook/Merchant - 20251011112853.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = [(str(row['Number']), row['Name']) for row in reader]
    
    print(f"Found {len(data)} merchants in CSV")
    
    # Step 3: Insert all merchants
    print("Inserting merchants...")
    cursor.executemany(
        "INSERT INTO merchant_mapping (merchant_id, merchant_name) VALUES (%s, %s)",
        data
    )
    conn.commit()
    print(f"✓ Inserted {len(data)} merchants")
    
    # Step 4: Verify
    cursor.execute("SELECT COUNT(*) FROM merchant_mapping")
    total = cursor.fetchone()[0]
    print(f"\n✓ Total merchants in table: {total}")
    
    # Step 5: Update transactions table
    print("\nUpdating transactions with merchant names...")
    cursor.execute("""
        UPDATE transactions t
        SET merchant_name = m.merchant_name
        FROM merchant_mapping m
        WHERE t.merchant_id = m.merchant_id
    """)
    updated = cursor.rowcount
    conn.commit()
    print(f"✓ Updated {updated} transactions")
    
    # Step 6: Show summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(merchant_name) as with_merchant_name
        FROM transactions
    """)
    result = cursor.fetchone()
    print(f"\n=== Summary ===")
    print(f"Total transactions: {result[0]}")
    print(f"With merchant names: {result[1]}")
    
    # Step 7: Show top 10 merchants
    print("\n=== Top 10 Merchant IDs by transaction count ===")
    cursor.execute("""
        SELECT merchant_id, merchant_name, COUNT(*) as count
        FROM transactions
        WHERE merchant_name IS NOT NULL
        GROUP BY merchant_id, merchant_name
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}: {row[2]} transactions")
    
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()

print("\n✓ Complete!")
