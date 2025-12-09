#!/bin/bash
# Script to start the Flask server

echo "Starting Market Data Query Interface..."
echo "========================================"
echo ""
echo "Make sure you have:"
echo "1. Installed dependencies: pip install -r requirements.txt"
echo "2. MySQL database is running"
echo "3. Database 'market_data' exists and has data"
echo ""
echo "Starting Flask server on http://127.0.0.1:5000/"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py

