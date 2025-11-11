#!/usr/bin/env python3
"""
BIN Bank Mapping Import Script
"""

import csv
import psycopg2
from psycopg2.extras import execute_batch

DB_CONFIG = {
    'dbname': 'payment_transactions',
    'user': 'webhook_user',
    'password': 'yingyanganil5s',
    'host': 'localhost',
    'port': '5432'
}

def import_bin_data(csv_file_path):
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("Clearing existing BIN data...")
        cursor.execute("DELETE FROM bin_bank_mapping;")
        
        print(f"Reading CSV file: {csv_file_path}")
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        print(f"Found {len(data)} BINs to import")
        
        insert_data = []
        for row in data:
            bin_number = str(row.get('BIN', '')).strip()
            bank_name = str(row.get('BankName', '')).strip()
            card_scheme = str(row.get('CardScheme', '')).strip()
            
            if bin_number and bank_name and card_scheme:
                insert_data.append((bin_number, bank_name, card_scheme))
        
        print(f"Clean records to insert: {len(insert_data)}")
        
        print("Inserting data...")
        insert_query = """
        INSERT INTO bin_bank_mapping (bin, bank_name, card_brand)
        VALUES (%s, %s, %s)
        ON CONFLICT (bin) DO UPDATE SET
            bank_name = EXCLUDED.bank_name,
            card_brand = EXCLUDED.card_brand;
        """
        
        execute_batch(cursor, insert_query, insert_data, page_size=100)
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM bin_bank_mapping;")
        total = cursor.fetchone()[0]
        print(f"\n✓ Successfully imported {total} BINs")
        
        cursor.execute("""
            SELECT card_brand, COUNT(*) as count 
            FROM bin_bank_mapping 
            GROUP BY card_brand 
            ORDER BY count DESC;
        """)
        
        print("\nCard Scheme Breakdown:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} BINs")
        
        cursor.execute("SELECT * FROM bin_bank_mapping WHERE bin = '540709';")
        test_result = cursor.fetchone()
        if test_result:
            print(f"\nTest BIN (540709): {test_result[2]} - {test_result[4]}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    csv_file = '/opt/payment-webhook/BINS_and_BANKS_List.csv'
    import_bin_data(csv_file)
    print("\n✓ Import complete!")
