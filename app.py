from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
import os

# Optional: load .env automatically if python-dotenv is installed
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- LLM imports / setup (Claude) ---
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # We'll handle this gracefully below

APP_VERSION = "v11-llm-env-vars"

app = Flask(__name__, static_folder="static")

# Allow frontend (same machine) to call API
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        },
        r"/*": {"origins": "*"},
    },
)

# =========================
# Environment variables
# =========================

# Anthropic API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

anthropic_client = (
    Anthropic(api_key=ANTHROPIC_API_KEY) if (Anthropic and ANTHROPIC_API_KEY) else None
)

print("DEBUG Anthropic imported?:", bool(Anthropic))
print("DEBUG API key present?:", bool(ANTHROPIC_API_KEY))
print("DEBUG anthropic_client created?:", bool(anthropic_client))
print("DEBUG model:", ANTHROPIC_MODEL)

# Database configuration from env
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "market_data"),
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None


# =========================
# LLM (Claude) SQL generator
# =========================

DB_SCHEMA_DESCRIPTION = """
You are an assistant that translates natural language questions into SQL for a MySQL database.
The database schema is:

Table: AssetType
- asset_type_id INT PRIMARY KEY
- name VARCHAR(20)
- description VARCHAR(255)

Table: Asset
- asset_id INT PRIMARY KEY
- name VARCHAR(50)
- symbol VARCHAR(20)
- asset_type_id INT REFERENCES AssetType(asset_type_id)
- base_currency CHAR(3)

Table: DailyMarketData
- asset_id INT REFERENCES Asset(asset_id)
- obs_date DATE
- price DECIMAL(18,4)
- volume BIGINT
Primary key: (asset_id, obs_date)
Constraints: price > 0, volume IS NULL OR volume >= 0
"""


def get_asset_reference_list():
    """
    Fetch the list of assets to show the LLM what actually exists.
    Returns a list of dicts: {asset_id, name, symbol}.
    """
    conn = get_db_connection()
    if not conn:
        print("WARNING: Could not connect to DB to fetch asset list.")
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT asset_id, name, symbol FROM Asset ORDER BY asset_id")
        rows = cursor.fetchall()
        return rows
    except mysql.connector.Error as e:
        print(f"ERROR fetching asset reference list: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def is_safe_sql(sql: str) -> bool:
    """Basic safety check: only allow simple SELECT statements."""
    if not sql:
        return False

    normalized = " ".join(sql.strip().lower().split())

    # Disallow dangerous stuff
    forbidden_tokens = [
        " insert ",
        " update ",
        " delete ",
        " drop ",
        " alter ",
        " truncate ",
        " create ",
        " grant ",
        " revoke ",
        " replace ",
        " merge ",
        "--",
        "/*",
        "*/",
    ]
    if any(tok in normalized for tok in forbidden_tokens):
        return False

    if ";" in normalized.strip().rstrip(";"):
        return False

    if not normalized.startswith("select"):
        return False

    return True


def generate_sql_from_llm(user_query: str) -> str:
    """Call Claude to generate a SQL query from the user question."""
    if not anthropic_client:
        raise RuntimeError(
            "Anthropic client not configured. "
            "Make sure 'anthropic' is installed and ANTHROPIC_API_KEY is set."
        )

    assets = get_asset_reference_list()
    if assets:
        asset_reference_text = "\n".join(
            f"- id {row['asset_id']}: {row['name']} (symbol: {row['symbol']})"
            for row in assets
        )
    else:
        asset_reference_text = "WARNING: Could not load assets from the database."

    prompt = f"""
You are a MySQL expert. Given a user's question and the database schema, write a single
safe SQL SELECT query that answers the question.

Here is the ACTUAL list of assets in the database:
{asset_reference_text}

Important rules about assets:
- ALWAYS identify assets using Asset.symbol in WHERE clauses (e.g., 'AAPL', 'TSLA', 'BTC').
- You may use Asset.name in SELECT lists, but NOT in filters.
- Never guess asset names that are not in the list above.
- If the user says "Apple", map it to the asset whose name or symbol best matches
  (in this case 'Apple Inc.' with symbol 'AAPL') from the list above.
- If you cannot confidently map the user's wording to one of the assets, return:
  SELECT 'Cannot answer this question from the available data' AS message;

General rules:
- Only use the tables and columns from the schema.
- NEVER modify data: no INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, etc.
- Only output the SQL query, nothing else.
- Prefer using Asset.symbol to identify assets instead of numeric ids.

Database schema:
{DB_SCHEMA_DESCRIPTION}

User question:
{user_query}
""".strip()

    resp = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    )

    text = resp.content[0].text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("sql\n"):
            text = text[4:]
        text = text.strip()

    print("Generated SQL from LLM:", text)  # helpful for debugging
    return text


def run_sql(sql: str):
    """Execute raw SQL and return rows or an error string."""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows, None
    except mysql.connector.Error as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


# =========================
# API routes
# =========================


@app.route("/api/query", methods=["POST", "OPTIONS"])
def handle_query():
    """Handle natural language query using Claude-generated SQL only."""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    user_query = (data.get("query") or "").strip()

    if not user_query:
        return jsonify({"success": False, "error": "Query is required"}), 400


    try:
        sql = generate_sql_from_llm(user_query)
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"LLM error: {e}",
                }
            ),
            500,
        )


    if not is_safe_sql(sql):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Generated SQL was rejected as unsafe.",
                    "sql": sql,
                }
            ),
            400,
        )


    rows, db_error = run_sql(sql)
    if db_error:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Database error: {db_error}",
                    "sql": sql,
                }
            ),
            500,
        )

    resp = {
        "success": True,
        "message": f"LLM-generated query executed successfully. Returned {len(rows)} row(s).",
        "sql": sql,
        "data": rows,
    }
    response = jsonify(resp)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/api/assets", methods=["GET", "OPTIONS"])
def get_assets():
    """Get list of all assets (non-LLM helper endpoint)."""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT a.asset_id, a.name, a.symbol, at.name as type_name
            FROM Asset a
            JOIN AssetType at ON a.asset_type_id = at.asset_type_id
            ORDER BY a.name
        """
        )
        assets = cursor.fetchall()
        response = jsonify({"success": True, "data": assets})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "version": APP_VERSION,
            "llm_enabled": bool(anthropic_client),
            "model": ANTHROPIC_MODEL,
        }
    )


@app.route("/")
def index():
    """Serve the main HTML page with no-cache headers."""
    response = send_file(os.path.join(app.static_folder, "index.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/style.css")
def serve_css():
    """Serve CSS file with no-cache headers."""
    try:
        response = send_file(
            os.path.join(app.static_folder, "style.css"), mimetype="text/css"
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        print(f"Error serving CSS: {e}")
        return "", 404


@app.route("/script.js")
def serve_js():
    """Serve JavaScript file with no-cache headers."""
    try:
        response = send_file(
            os.path.join(app.static_folder, "script.js"),
            mimetype="application/javascript",
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        print(f"Error serving JS: {e}")
        return "", 404


@app.route("/favicon.ico")
def favicon():
    """Serve favicon (return 204 No Content to avoid 404)."""
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", "5001"))
    print("Starting Flask server...")
    print("Open your browser and navigate to:")
    print(f"  http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host="127.0.0.1", port=port, threaded=True)
