# Market Data Database System

A relational database system for storing and managing 5-year time series market data for commodities, cryptocurrencies, indices, and equities.

## Overview

This project normalizes a wide CSV dataset (one row per date with many price/volume columns) into a normalized relational database structure with three main tables: `AssetType`, `Asset`, and `DailyMarketData`.

### Dataset Information

- **Time Period**: February 4, 2019 to February 2, 2024 (1,243 trading days)
- **Total Records**: 23,616 daily market data records
- **Assets Covered**: 19 assets across 4 categories
  - **Commodities** (7): Natural Gas, Crude Oil, Copper, Gold, Silver, Platinum
  - **Cryptocurrencies** (2): Bitcoin, Ethereum
  - **Indices** (2): S&P 500, Nasdaq 100
  - **Equities** (8): Apple, Tesla, Microsoft, Google, Nvidia, Berkshire, Netflix, Amazon, Meta

## Project Structure

```
db final/
├── README.md                      # This file
├── requirements.txt                # Python dependencies
├── create_database.sql            # Database creation script
├── create_schema.sql              # Complete schema with tables and initial data
├── load_data.py                   # Python script to load CSV data into database
├── download_dataset.py            # Script to download dataset from Kaggle
├── inspect_database.py            # Script to inspect database contents
├── query_all_data.sql             # Sample SQL queries
└── Stock Market Dataset.csv       # Source dataset (to be pushed later)
```

## Prerequisites

- **MySQL Server** (version 5.7+ or 8.0+)
- **Python** 3.7+ (with conda/miniconda recommended)
- **MySQL credentials** (username and password)
- **Kaggle API credentials** (if downloading dataset fresh)

## Setup Instructions

### 1. Clone Repository and Navigate to Project

```bash
cd "path/to/db final"
```

### 2. Set Up Python Environment

```bash
# Create conda environment (if not already created)
conda create -n dat-bot-311 python=3.11

# Activate environment
conda activate dat-bot-311

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Database Connection

Edit `load_data.py` and update the database configuration:

```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'your_username',      # Update this
    'password': 'your_password',   # Update this
    'database': 'market_data'
}
```

### 4. Create Database Schema

Run the SQL schema file to create the database and tables:

**Option A: Using MySQL command line**
```bash
mysql -u your_username -p < create_schema.sql
```

**Option B: Using a database client**
- Open `create_schema.sql` in your MySQL client (e.g., MySQL Workbench, DBeaver, dbclient)
- Execute the entire script

This will:
- Create the `market_data` database
- Create three tables: `AssetType`, `Asset`, `DailyMarketData`
- Insert initial data for asset types and assets

### 5. Load Data from CSV

**If you have the CSV file:**

```bash
python load_data.py
```

This script will:
- Read `Stock Market Dataset.csv`
- Parse dates from DD-MM-YYYY format
- Handle numbers with commas (e.g., "43,194.70")
- Insert all records into `DailyMarketData` table
- Show progress every 100 rows

**If you need to download the dataset:**

1. Set up Kaggle API credentials:
   - Go to https://www.kaggle.com/account
   - Create API token (downloads `kaggle.json`)
   - Place it in `C:\Users\<username>\.kaggle\kaggle.json` (Windows) or `~/.kaggle/kaggle.json` (Linux/Mac)

2. Download the dataset:
   ```bash
   python download_dataset.py
   ```

3. Then load the data:
   ```bash
   python load_data.py
   ```

## Frontend for Market Data Query Interface

A modern web interface for querying market data using natural language.

### Features

- **Natural Language Queries**: Ask questions in plain English about market data
- **Modern UI**: Clean, responsive design with gradient styling
- **Real-time Feedback**: Get instant responses to your queries
- **Example Queries**: Click on example tags to quickly try different queries

### Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**:
   Make sure your MySQL database is running and update the `DB_CONFIG` in `app.py` if needed:
   ```python
   DB_CONFIG = {
       'host': '127.0.0.1',
       'port': 3306,
       'user': 'root',
       'password': '',  # Update if needed
       'database': 'market_data'
   }
   ```

3. **Run the Flask Server**:
   ```bash
   python app.py
   ```

4. **Open in Browser**:
   Navigate to `http://127.0.0.1:8000/` in your web browser

## Database Schema

### Table: AssetType

Categorizes assets into types.

| Column | Type | Description |
|--------|------|-------------|
| asset_type_id | INT (PK) | Primary key |
| name | VARCHAR(20) | Type name (COMMODITY, CRYPTO, INDEX, EQUITY) |
| description | VARCHAR(255) | Type description |

### Table: Asset

Represents each financial instrument.

| Column | Type | Description |
|--------|------|-------------|
| asset_id | INT (PK) | Primary key |
| name | VARCHAR(50) | Asset name (e.g., "Natural Gas", "Bitcoin") |
| symbol | VARCHAR(20) | Trading symbol (e.g., "NATGAS", "BTC") |
| asset_type_id | INT (FK) | Foreign key to AssetType |
| base_currency | CHAR(3) | Currency code (default: 'USD') |

### Table: DailyMarketData

Time series fact table storing daily price and volume data.

| Column | Type | Description |
|--------|------|-------------|
| asset_id | INT (FK) | Foreign key to Asset |
| obs_date | DATE | Observation date (YYYY-MM-DD) |
| price | DECIMAL(18,4) | Price in base currency |
| volume | BIGINT | Trading volume (NULL if not available) |

**Constraints:**
- Primary Key: (asset_id, obs_date)
- Foreign Key: asset_id → Asset(asset_id)
- Check: price > 0
- Check: volume IS NULL OR volume >= 0

## Verification

After loading data, verify the setup:

```bash
python inspect_database.py
```

This will display:
- Asset types and assets
- Record counts per asset
- Date ranges
- Sample data
- Volume statistics

Expected output:
- **Total records**: 23,616
- **Unique dates**: 1,243
- **Date range**: 2019-02-04 to 2024-02-02
- **Records per asset**: ~1,243 (varies slightly due to missing data)

## Sample Queries

See `query_all_data.sql` for example queries, or try:

```sql
-- Get all data for Bitcoin
SELECT a.name, dmd.obs_date, dmd.price, dmd.volume
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
WHERE a.symbol = 'BTC'
ORDER BY dmd.obs_date DESC;

-- Get average prices by asset type
SELECT at.name as asset_type, AVG(dmd.price) as avg_price
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
JOIN AssetType at ON a.asset_type_id = at.asset_type_id
GROUP BY at.name;

-- Find highest price for each asset
SELECT a.name, a.symbol, MAX(dmd.price) as max_price, 
       MAX(dmd.obs_date) as date_of_max_price
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
GROUP BY a.asset_id, a.name, a.symbol
ORDER BY max_price DESC;
```

## Troubleshooting

### Issue: "Can't connect to MySQL server"
- Verify MySQL server is running
- Check host, port, username, and password in `load_data.py`
- Ensure MySQL allows connections from your IP

### Issue: "ModuleNotFoundError"
- Activate conda environment: `conda activate dat-bot-311`
- Install dependencies: `pip install -r requirements.txt`

### Issue: "Access denied for user"
- Verify MySQL credentials
- Ensure user has CREATE DATABASE and INSERT privileges

### Issue: "Duplicate entry" errors
- The script uses `ON DUPLICATE KEY UPDATE`, so re-running is safe
- If issues persist, truncate the table: `TRUNCATE TABLE DailyMarketData;`

### Issue: Limited rows visible in database client
- Check client's "Max Rows" or "Row Limit" setting
- Remove LIMIT clauses from queries
- Use pagination if available

## Data Notes

- **Date Format**: CSV dates (DD-MM-YYYY) are converted to MySQL DATE format (YYYY-MM-DD)
- **Missing Volumes**: Some assets (especially indices like S&P 500) don't have volume data - stored as NULL
- **Number Formatting**: Prices with commas (e.g., "43,194.70") are automatically cleaned
- **Data Completeness**: Most assets have ~1,243 records, but some may have fewer due to missing data points

## Files Description

- **create_schema.sql**: Complete database schema with initial data
- **load_data.py**: Data loading script with error handling and progress tracking
- **download_dataset.py**: Downloads dataset from Kaggle and moves to project directory
- **inspect_database.py**: Database inspection and verification tool
- **query_all_data.sql**: Sample SQL queries for common operations

## Next Steps

- [ ] Push CSV dataset to repository
- [ ] Add data validation scripts
- [ ] Create data analysis queries
- [ ] Add indexes for performance optimization
- [ ] Create backup/restore scripts

## Contributors

Charles Weng
Cassie Zhang

