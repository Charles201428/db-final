from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
import re
import os

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for frontend

# Database connection configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'market_data'
}

# Asset name mappings for natural language processing
ASSET_NAMES = {
    'natural gas': 1, 'gas': 1,
    'crude oil': 2, 'oil': 2,
    'copper': 3,
    'bitcoin': 4, 'btc': 4,
    'ethereum': 5, 'eth': 5,
    's&p 500': 6, 'sp500': 6, 's&p500': 6, 'sp 500': 6,
    'nasdaq': 7, 'nasdaq 100': 7,
    'apple': 8, 'aapl': 8,
    'tesla': 9, 'tsla': 9,
    'microsoft': 10, 'msft': 10,
    'silver': 18,
    'google': 11, 'googl': 11, 'alphabet': 11,
    'nvidia': 12, 'nvda': 12,
    'berkshire': 13, 'brk': 13, 'berkshire hathaway': 13,
    'netflix': 14, 'nflx': 14,
    'amazon': 15, 'amzn': 15,
    'meta': 16, 'facebook': 16, 'fb': 16,
    'gold': 17,
    'platinum': 19
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def parse_natural_language_query(query):
    """Parse natural language query and extract intent"""
    query_lower = query.lower()
    
    # Extract asset name
    asset_id = None
    asset_name = None
    for name, aid in ASSET_NAMES.items():
        if name in query_lower:
            asset_id = aid
            asset_name = name
            break
    
    # Detect query type
    if any(word in query_lower for word in ['price', 'cost', 'value', 'worth', 'trading at']):
        query_type = 'price'
    elif any(word in query_lower for word in ['volume', 'vol', 'traded', 'shares']):
        query_type = 'volume'
    elif any(word in query_lower for word in ['max', 'maximum', 'highest', 'peak', 'top']):
        query_type = 'max'
    elif any(word in query_lower for word in ['min', 'minimum', 'lowest', 'bottom']):
        query_type = 'min'
    elif any(word in query_lower for word in ['average', 'avg', 'mean']):
        query_type = 'average'
    elif any(word in query_lower for word in ['recent', 'latest', 'current', 'today', 'now']):
        query_type = 'recent'
    elif any(word in query_lower for word in ['all', 'list', 'show', 'display']):
        query_type = 'list'
    else:
        query_type = 'general'
    
    # Extract date if mentioned
    date_pattern = r'(\d{4})-(\d{2})-(\d{2})|(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
    date_match = re.search(date_pattern, query)
    target_date = None
    if date_match:
        # Try to parse date
        try:
            if date_match.group(1):  # YYYY-MM-DD format
                target_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            else:  # MM/DD/YYYY format
                month, day, year = date_match.group(4), date_match.group(5), date_match.group(6)
                if len(year) == 2:
                    year = '20' + year
                target_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
    
    return {
        'asset_id': asset_id,
        'asset_name': asset_name,
        'query_type': query_type,
        'target_date': target_date
    }

def execute_query(parsed):
    """Execute SQL query based on parsed natural language"""
    conn = get_db_connection()
    if not conn:
        return {
            'success': False,
            'error': 'Database connection failed.'
        }
    
    cursor = conn.cursor(dictionary=True)
    result = {'success': True, 'data': [], 'message': ''}
    
    try:
        if parsed['query_type'] == 'list':
            # List all assets
            cursor.execute("""
                SELECT a.asset_id, a.name, a.symbol, at.name as type_name
                FROM Asset a
                JOIN AssetType at ON a.asset_type_id = at.asset_type_id
                ORDER BY a.name
            """)
            result['data'] = cursor.fetchall()
            result['message'] = f"Found {len(result['data'])} assets"
        
        elif parsed['asset_id']:
            asset_id = parsed['asset_id']
            
            if parsed['query_type'] == 'recent':
                # Get most recent data
                cursor.execute("""
                    SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s
                    ORDER BY dmd.obs_date DESC
                    LIMIT 10
                """, (asset_id,))
                result['data'] = cursor.fetchall()
                result['message'] = f"Recent data for {parsed['asset_name']}"
            
            elif parsed['query_type'] == 'max':
                # Get maximum price
                cursor.execute("""
                    SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s AND dmd.price IS NOT NULL
                    ORDER BY dmd.price DESC
                    LIMIT 1
                """, (asset_id,))
                result['data'] = cursor.fetchall()
                if result['data']:
                    result['message'] = f"Highest price for {parsed['asset_name']}: ${result['data'][0]['price']:.2f} on {result['data'][0]['obs_date']}"
            
            elif parsed['query_type'] == 'min':
                # Get minimum price
                cursor.execute("""
                    SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s AND dmd.price IS NOT NULL
                    ORDER BY dmd.price ASC
                    LIMIT 1
                """, (asset_id,))
                result['data'] = cursor.fetchall()
                if result['data']:
                    result['message'] = f"Lowest price for {parsed['asset_name']}: ${result['data'][0]['price']:.2f} on {result['data'][0]['obs_date']}"
            
            elif parsed['query_type'] == 'average':
                # Get average price
                cursor.execute("""
                    SELECT AVG(dmd.price) as avg_price, COUNT(*) as count, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s AND dmd.price IS NOT NULL
                """, (asset_id,))
                row = cursor.fetchone()
                if row and row['avg_price']:
                    result['data'] = [row]
                    result['message'] = f"Average price for {parsed['asset_name']}: ${row['avg_price']:.2f} (based on {row['count']} records)"
            
            elif parsed['target_date']:
                # Get data for specific date
                cursor.execute("""
                    SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s AND dmd.obs_date = %s
                """, (asset_id, parsed['target_date']))
                result['data'] = cursor.fetchall()
                if result['data']:
                    row = result['data'][0]
                    result['message'] = f"{parsed['asset_name']} on {parsed['target_date']}: Price ${row['price']:.2f}, Volume {row['volume'] if row['volume'] else 'N/A'}"
                else:
                    result['message'] = f"No data found for {parsed['asset_name']} on {parsed['target_date']}"
            
            else:
                # General query - get recent data
                cursor.execute("""
                    SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                    FROM DailyMarketData dmd
                    JOIN Asset a ON dmd.asset_id = a.asset_id
                    WHERE dmd.asset_id = %s
                    ORDER BY dmd.obs_date DESC
                    LIMIT 20
                """, (asset_id,))
                result['data'] = cursor.fetchall()
                result['message'] = f"Data for {parsed['asset_name']}"
        
        else:
            # No specific asset - show general info
            cursor.execute("""
                SELECT COUNT(*) as total_records,
                       MIN(obs_date) as earliest_date,
                       MAX(obs_date) as latest_date
                FROM DailyMarketData
            """)
            result['data'] = cursor.fetchall()
            result['message'] = "Database contains market data from various assets"
    
    except mysql.connector.Error as e:
        result['success'] = False
        result['error'] = str(e)
        result['message'] = f"Database error: {str(e)}"
    
    finally:
        cursor.close()
        conn.close()
    
    return result

@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handle natural language query"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'}), 400
    
    # Parse the natural language query
    parsed = parse_natural_language_query(query)
    
    # Execute the query
    result = execute_query(parsed)
    
    return jsonify(result)

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get list of all assets"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.asset_id, a.name, a.symbol, at.name as type_name
            FROM Asset a
            JOIN AssetType at ON a.asset_type_id = at.asset_type_id
            ORDER BY a.name
        """)
        assets = cursor.fetchall()
        return jsonify({'success': True, 'data': assets})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/style.css')
def serve_css():
    """Serve CSS file"""
    return send_file(os.path.join(app.static_folder, 'style.css'))

@app.route('/script.js')
def serve_js():
    """Serve JavaScript file"""
    return send_file(os.path.join(app.static_folder, 'script.js'))

@app.route('/favicon.ico')
def favicon():
    """Serve favicon (return 204 No Content to avoid 404)"""
    return '', 204

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open your browser and navigate to:")
    print("  http://localhost:5000")
    print("  or http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)

