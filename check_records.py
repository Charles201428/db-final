import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'market_data'
}

def check_records():
    """Check total records and sample queries"""
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("Checking DailyMarketData table...")
    print("=" * 60)
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM DailyMarketData")
    total = cursor.fetchone()['total']
    print(f"Total records in table: {total:,}")
    
    # Count for asset_id = 1 (Natural Gas)
    cursor.execute("SELECT COUNT(*) as total FROM DailyMarketData WHERE asset_id = 1")
    natgas_total = cursor.fetchone()['total']
    print(f"Records for asset_id = 1 (Natural Gas): {natgas_total:,}")
    
    # Date range for asset_id = 1
    cursor.execute("""
        SELECT MIN(obs_date) as first_date, MAX(obs_date) as last_date
        FROM DailyMarketData 
        WHERE asset_id = 1
    """)
    date_range = cursor.fetchone()
    print(f"Date range for Natural Gas: {date_range['first_date']} to {date_range['last_date']}")
    
    # Check if there are records after 2019-06-26
    cursor.execute("""
        SELECT COUNT(*) as count_after 
        FROM DailyMarketData 
        WHERE asset_id = 1 AND obs_date > '2019-06-26'
    """)
    after_count = cursor.fetchone()['count_after']
    print(f"Records after 2019-06-26: {after_count:,}")
    
    # Show a few records after 2019-06-26
    print("\nSample records after 2019-06-26:")
    cursor.execute("""
        SELECT asset_id, obs_date, price, volume
        FROM DailyMarketData 
        WHERE asset_id = 1 AND obs_date > '2019-06-26'
        ORDER BY obs_date
        LIMIT 10
    """)
    samples = cursor.fetchall()
    for row in samples:
        print(f"  {row['obs_date']}: price={row['price']}, volume={row['volume']}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_records()

