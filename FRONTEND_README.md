# Frontend for Market Data Query Interface

A modern web interface for querying market data using natural language.

## Features

- **Natural Language Queries**: Ask questions in plain English about market data
- **Modern UI**: Clean, responsive design with gradient styling
- **Real-time Feedback**: Get instant responses to your queries
- **Example Queries**: Click on example tags to quickly try different queries

## Setup

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
   Navigate to `http://127.0.0.1:5000/` in your web browser

## Example Queries

- "What is the price of Bitcoin?"
- "Show me the highest price for Apple"
- "What is the average price of Gold?"
- "List all assets"
- "Show recent data for Tesla"
- "What was the price of Microsoft on 2020-01-15?"

## Query Types Supported

The system can understand various query types:

- **Price queries**: "price", "cost", "value", "worth"
- **Volume queries**: "volume", "vol", "traded"
- **Maximum queries**: "max", "maximum", "highest", "peak"
- **Minimum queries**: "min", "minimum", "lowest"
- **Average queries**: "average", "avg", "mean"
- **Recent queries**: "recent", "latest", "current"
- **List queries**: "all", "list", "show", "display"

## Supported Assets

The system recognizes various asset names and symbols:
- Commodities: Natural Gas, Crude Oil, Copper, Gold, Silver, Platinum
- Cryptocurrencies: Bitcoin (BTC), Ethereum (ETH)
- Indices: S&P 500, Nasdaq 100
- Equities: Apple, Tesla, Microsoft, Google, Nvidia, Berkshire, Netflix, Amazon, Meta

## API Endpoints

- `GET /` - Main frontend page
- `POST /api/query` - Submit a natural language query
- `GET /api/assets` - Get list of all assets
- `GET /health` - Health check endpoint

## Project Structure

```
db-final/
├── app.py                 # Flask backend server
├── static/
│   ├── index.html        # Main HTML page
│   ├── style.css         # Styling
│   └── script.js         # Frontend JavaScript
└── requirements.txt      # Python dependencies
```

