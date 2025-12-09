# Setting Up Local MySQL Database

## Current Status

✅ MySQL/MariaDB is installed on your system
❌ MySQL server is not currently running

## Option 1: Start MySQL Server (if you have admin access)

If you have access to start services, run:
```bash
sudo systemctl start mariadb
# or
sudo systemctl start mysql
```

To enable MySQL to start automatically on boot:
```bash
sudo systemctl enable mariadb
```

## Option 2: Use School Database Server

Since you're on a school server where sudo is disabled, you might want to use the school's database server instead. The configuration is already set up for:

- **Host**: `dbase.cs.jhu.edu`
- **User**: `FA25_xiyanzhang2`
- **Database**: `FA25_xiyanzhang2_db`

To switch back to school server, update `app.py`:
```python
DB_CONFIG = {
    'host': 'dbase.cs.jhu.edu',
    'port': 3306,
    'user': 'FA25_xiyanzhang2',
    'password': 'pMvd80BhRR',
    'database': 'FA25_xiyanzhang2_db'
}
```

## Option 3: Create Database on School Server

If you want to use the school server but need to create the `market_data` database:

1. Connect to school database:
   ```bash
   mysql -h dbase.cs.jhu.edu -u FA25_xiyanzhang2 -p
   # Password: pMvd80BhRR
   ```

2. Create the database and tables:
   ```bash
   mysql -h dbase.cs.jhu.edu -u FA25_xiyanzhang2 -p < create_schema.sql
   ```

3. Load the data:
   ```bash
   python3 load_data.py
   ```
   (Make sure to update `load_data.py` with school server credentials first)

## Verify Database Connection

Test the connection:
```bash
python3 -c "
import mysql.connector
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='',
    database='market_data'
)
print('✓ Connected successfully!')
conn.close()
"
```

## Next Steps

1. **If using local MySQL**: Start the MySQL service and create the database
2. **If using school server**: Update the credentials in `app.py` and ensure the database exists
3. **Create the database schema**: Run `create_schema.sql` to set up tables
4. **Load data**: Run `load_data.py` to populate the database
5. **Start Flask app**: Run `python3 app.py`

