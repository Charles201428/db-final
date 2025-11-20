import mysql.connector
from tabulate import tabulate

# Database connection configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'market_data'
}

def inspect_database():
    """Inspect what was created in the database"""
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print("=" * 60)
        print("DATABASE INSPECTION REPORT")
        print("=" * 60)
        
        # 1. Check AssetType table
        print("\n1. ASSET TYPE TABLE:")
        print("-" * 60)
        cursor.execute("SELECT * FROM AssetType ORDER BY asset_type_id")
        asset_types = cursor.fetchall()
        print(tabulate(asset_types, headers="keys", tablefmt="grid"))
        
        # 2. Check Asset table
        print("\n2. ASSET TABLE:")
        print("-" * 60)
        cursor.execute("""
            SELECT a.asset_id, a.name, a.symbol, at.name as type_name, a.base_currency
            FROM Asset a
            JOIN AssetType at ON a.asset_type_id = at.asset_type_id
            ORDER BY a.asset_id
        """)
        assets = cursor.fetchall()
        print(tabulate(assets, headers="keys", tablefmt="grid"))
        
        # 3. Check DailyMarketData statistics
        print("\n3. DAILY MARKET DATA STATISTICS:")
        print("-" * 60)
        
        # Total records
        cursor.execute("SELECT COUNT(*) as total FROM DailyMarketData")
        total = cursor.fetchone()['total']
        print(f"Total records: {total:,}")
        
        # Records per asset
        cursor.execute("""
            SELECT a.name, a.symbol, COUNT(dmd.obs_date) as record_count,
                   MIN(dmd.obs_date) as first_date, MAX(dmd.obs_date) as last_date
            FROM Asset a
            LEFT JOIN DailyMarketData dmd ON a.asset_id = dmd.asset_id
            GROUP BY a.asset_id, a.name, a.symbol
            ORDER BY a.asset_id
        """)
        asset_stats = cursor.fetchall()
        print("\nRecords per Asset:")
        print(tabulate(asset_stats, headers="keys", tablefmt="grid"))
        
        # Date range
        cursor.execute("""
            SELECT MIN(obs_date) as earliest_date, MAX(obs_date) as latest_date,
                   COUNT(DISTINCT obs_date) as unique_dates
            FROM DailyMarketData
        """)
        date_range = cursor.fetchone()
        print("\nDate Range:")
        print(tabulate([date_range], headers="keys", tablefmt="grid"))
        
        # Sample data
        print("\n4. SAMPLE DATA (First 10 records):")
        print("-" * 60)
        cursor.execute("""
            SELECT a.name, a.symbol, dmd.obs_date, dmd.price, dmd.volume
            FROM DailyMarketData dmd
            JOIN Asset a ON dmd.asset_id = a.asset_id
            ORDER BY dmd.obs_date DESC, a.asset_id
            LIMIT 10
        """)
        samples = cursor.fetchall()
        print(tabulate(samples, headers="keys", tablefmt="grid"))
        
        # Volume statistics
        print("\n5. VOLUME STATISTICS:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(volume) as records_with_volume,
                COUNT(*) - COUNT(volume) as records_without_volume
            FROM DailyMarketData
        """)
        vol_stats = cursor.fetchone()
        print(tabulate([vol_stats], headers="keys", tablefmt="grid"))
        
        # Assets without volume
        cursor.execute("""
            SELECT a.name, a.symbol, COUNT(*) as records_without_volume
            FROM Asset a
            JOIN DailyMarketData dmd ON a.asset_id = dmd.asset_id
            WHERE dmd.volume IS NULL
            GROUP BY a.asset_id, a.name, a.symbol
        """)
        no_vol = cursor.fetchall()
        if no_vol:
            print("\nAssets with NULL volume (expected for indices):")
            print(tabulate(no_vol, headers="keys", tablefmt="grid"))
        
        print("\n" + "=" * 60)
        print("INSPECTION COMPLETE")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == '__main__':
    inspect_database()

