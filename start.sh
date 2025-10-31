#!/bin/bash

# Agreement Map - Quick Start Script

echo "🚀 Starting Agreement Map..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. You'll need to enter your API key in the app."
fi

# Start Streamlit
echo ""
echo "✅ Launching Agreement Map..."
echo "   Navigate to http://localhost:8501 in your browser"
echo ""
streamlit run app.py
