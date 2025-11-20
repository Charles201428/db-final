-- Query to see all DailyMarketData records
-- Remove or adjust LIMIT as needed

-- Option 1: View all records (may be slow for large datasets)
SELECT 
    a.name as asset_name,
    a.symbol,
    dmd.obs_date,
    dmd.price,
    dmd.volume
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
ORDER BY dmd.obs_date DESC, a.asset_id
LIMIT 10000;  -- Adjust this number or remove LIMIT entirely

-- Option 2: View all records for a specific asset (Natural Gas)
SELECT 
    a.name as asset_name,
    a.symbol,
    dmd.obs_date,
    dmd.price,
    dmd.volume
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
WHERE a.symbol = 'NATGAS'
ORDER BY dmd.obs_date DESC;

-- Option 3: Paginated query (get next 1000 records after a certain date)
SELECT 
    a.name as asset_name,
    a.symbol,
    dmd.obs_date,
    dmd.price,
    dmd.volume
FROM DailyMarketData dmd
JOIN Asset a ON dmd.asset_id = a.asset_id
WHERE dmd.asset_id = 1 AND dmd.obs_date > '2019-06-26'
ORDER BY dmd.obs_date
LIMIT 1000;

