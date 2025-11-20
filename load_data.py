import csv
import mysql.connector
from datetime import datetime
import re

# Database connection configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',  # Update with your MySQL username
    'password': '',  # Update with your MySQL password
    'database': 'market_data'
}

# Mapping of CSV column names to asset_id
# Format: (price_column, volume_column, asset_id)
ASSET_MAPPING = [
    ('Natural_Gas_Price', 'Natural_Gas_Vol.', 1),
    ('Crude_oil_Price', 'Crude_oil_Vol.', 2),
    ('Copper_Price', 'Copper_Vol.', 3),
    ('Bitcoin_Price', 'Bitcoin_Vol.', 4),
    ('Platinum_Price', 'Platinum_Vol.', 19),
    ('Ethereum_Price', 'Ethereum_Vol.', 5),
    ('S&P_500_Price', None, 6),  # No volume column
    ('Nasdaq_100_Price', 'Nasdaq_100_Vol.', 7),
    ('Apple_Price', 'Apple_Vol.', 8),
    ('Tesla_Price', 'Tesla_Vol.', 9),
    ('Microsoft_Price', 'Microsoft_Vol.', 10),
    ('Silver_Price', 'Silver_Vol.', 18),
    ('Google_Price', 'Google_Vol.', 11),
    ('Nvidia_Price', 'Nvidia_Vol.', 12),
    ('Berkshire_Price', 'Berkshire_Vol.', 13),
    ('Netflix_Price', 'Netflix_Vol.', 14),
    ('Amazon_Price', 'Amazon_Vol.', 15),
    ('Meta_Price', 'Meta_Vol.', 16),
    ('Gold_Price', 'Gold_Vol.', 17),
]

def clean_number(value):
    """Remove commas and convert to float, return None if empty"""
    if not value or value.strip() == '':
        return None
    # Remove commas and convert to float
    cleaned = value.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def parse_date(date_str):
    """Convert DD-MM-YYYY to YYYY-MM-DD"""
    try:
        dt = datetime.strptime(date_str.strip(), '%d-%m-%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        print(f"Warning: Could not parse date: {date_str}")
        return None

def load_csv_to_db(csv_file_path):
    """Load CSV data into MySQL database"""
    
    # Connect to database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Connected to database successfully")
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return
    
    # Read CSV file
    inserted_count = 0
    error_count = 0
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
            date_str = row.get('Date', '').strip()
            if not date_str:
                continue
            
            obs_date = parse_date(date_str)
            if not obs_date:
                error_count += 1
                continue
            
            # Process each asset
            for price_col, vol_col, asset_id in ASSET_MAPPING:
                price_val = clean_number(row.get(price_col, ''))
                
                # Skip if price is missing (required field)
                if price_val is None or price_val <= 0:
                    continue
                
                # Get volume (can be None)
                volume_val = None
                if vol_col:
                    vol_raw = clean_number(row.get(vol_col, ''))
                    if vol_raw is not None and vol_raw >= 0:
                        volume_val = int(vol_raw)
                
                # Insert into database
                try:
                    insert_query = """
                        INSERT INTO DailyMarketData (asset_id, obs_date, price, volume)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            price = VALUES(price),
                            volume = VALUES(volume)
                    """
                    cursor.execute(insert_query, (asset_id, obs_date, price_val, volume_val))
                    inserted_count += 1
                except mysql.connector.Error as err:
                    print(f"Error inserting row {row_num}, asset_id {asset_id}, date {obs_date}: {err}")
                    error_count += 1
            
            # Commit every 100 rows for better performance
            if inserted_count % 100 == 0:
                conn.commit()
                print(f"Processed {row_num} rows, inserted {inserted_count} records...")
    
    # Final commit
    conn.commit()
    print(f"\nData loading complete!")
    print(f"Total records inserted: {inserted_count}")
    print(f"Errors encountered: {error_count}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    csv_file = 'Stock Market Dataset.csv'
    print(f"Loading data from {csv_file}...")
    load_csv_to_db(csv_file)

