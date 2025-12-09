from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
import re
import os

APP_VERSION = "v7-debug-xyz"
app = Flask(__name__, static_folder='static')
CORS(app, resources={
    r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]},
    r"/*": {"origins": "*"}
})  # Enable CORS for frontend

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
        query_type = parsed.get('query_type')
        asset_id = parsed.get('asset_id')
        asset_name = parsed.get('asset_name')
        target_date = parsed.get('target_date')

        # 1. List queries (don't need a specific asset)
        if query_type == 'list':
            cursor.execute("""
                SELECT a.asset_id, a.name, a.symbol, at.name as type_name
                FROM Asset a
                JOIN AssetType at ON a.asset_type_id = at.asset_type_id
                ORDER BY a.name
            """)
            result['data'] = cursor.fetchall()
            result['message'] = f"Found {len(result['data'])} assets"
            return result

        # 2. No asset detected
        if not asset_id:
            # They clearly asked for a metric but no asset name
            if query_type in ['price', 'volume', 'max', 'min', 'average', 'recent']:
                result['success'] = False
                result['error'] = (
                    "I couldn't figure out which asset you're asking about. "
                    "Please include a specific asset name, e.g. "
                    "'What is the price of Bitcoin?', "
                    "'Show recent data for Tesla', or "
                    "'What is the average price of Gold?'."
                )
                result['message'] = ''
                return result

            # Completely general / illegible query
            result['success'] = False
            result['error'] = (
                "I couldn't understand that query. "
                "Try something like:\n"
                "• 'What is the price of Bitcoin?'\n"
                "• 'Show recent data for Tesla'\n"
                "• 'Show the highest price for Apple'\n"
                "• 'List all assets'"
            )
            result['message'] = ''
            return result

        # 3. Asset-specific queries
        if query_type == 'recent':
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
            result['message'] = f"Recent data for {asset_name}"

        elif query_type == 'max':
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
                row = result['data'][0]
                result['message'] = (
                    f"Highest price for {asset_name}: "
                    f"${row['price']:.2f} on {row['obs_date']}"
                )

        elif query_type == 'min':
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
                row = result['data'][0]
                result['message'] = (
                    f"Lowest price for {asset_name}: "
                    f"${row['price']:.2f} on {row['obs_date']}"
                )

        elif query_type == 'average':
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
                result['message'] = (
                    f"Average price for {asset_name}: "
                    f"${row['avg_price']:.2f} (based on {row['count']} records)"
                )

        elif target_date:
            # Get data for specific date
            cursor.execute("""
                SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                FROM DailyMarketData dmd
                JOIN Asset a ON dmd.asset_id = a.asset_id
                WHERE dmd.asset_id = %s AND dmd.obs_date = %s
            """, (asset_id, target_date))
            result['data'] = cursor.fetchall()
            if result['data']:
                row = result['data'][0]
                result['message'] = (
                    f"{asset_name} on {target_date}: "
                    f"Price ${row['price']:.2f}, "
                    f"Volume {row['volume'] if row['volume'] else 'N/A'}"
                )
            else:
                result['message'] = (
                    f"No data found for {asset_name} on {target_date}"
                )

        else:
            # General asset query - get recent data
            cursor.execute("""
                SELECT dmd.obs_date, dmd.price, dmd.volume, a.name, a.symbol
                FROM DailyMarketData dmd
                JOIN Asset a ON dmd.asset_id = a.asset_id
                WHERE dmd.asset_id = %s
                ORDER BY dmd.obs_date DESC
                LIMIT 20
            """, (asset_id,))
            result['data'] = cursor.fetchall()
            result['message'] = f"Data for {asset_name}"

    except mysql.connector.Error as e:
        result['success'] = False
        result['error'] = str(e)
        result['message'] = f"Database error: {str(e)}"
    
    finally:
        cursor.close()
        conn.close()
    
    return result

@app.route('/api/query', methods=['POST', 'OPTIONS'])
def handle_query():
    """Handle natural language query"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400
    
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'}), 400
    
    # Parse the natural language query
    parsed = parse_natural_language_query(query)
    
    # Execute the query
    result = execute_query(parsed)
    
    response = jsonify(result)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/assets', methods=['GET', 'OPTIONS'])
def get_assets():
    """Get list of all assets"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
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
        response = jsonify({'success': True, 'data': assets})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'version': APP_VERSION})

@app.route('/')
def index():
    """Serve the main HTML page with no-cache headers"""
    response = send_file(os.path.join(app.static_folder, 'index.html'))
    # Add headers to prevent caching during development
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Flask will automatically serve static files from the static_folder
# But we keep explicit routes for better control
@app.route('/style.css')
def serve_css():
    """Serve CSS file with no-cache headers"""
    try:
        response = send_file(os.path.join(app.static_folder, 'style.css'), mimetype='text/css')
        # Add headers to prevent caching during development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error serving CSS: {e}")
        return '', 404

@app.route('/script.js')
def serve_js():
    """Serve JavaScript file with no-cache headers"""
    try:
        response = send_file(os.path.join(app.static_folder, 'script.js'), mimetype='application/javascript')
        # Add headers to prevent caching during development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error serving JS: {e}")
        return '', 404

@app.route('/favicon.ico')
def favicon():
    """Serve favicon (return 204 No Content to avoid 404)"""
    return '', 204

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open your browser and navigate to:")
    print("  http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='127.0.0.1', port=8000, threaded=True)


