#!/bin/bash

# Automated Lead Management & Email Tracking System - Startup Script

echo "════════════════════════════════════════════════════════════"
echo " Lead Management & Email Tracking System"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo " Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo " Python found: $(python3 --version)"
echo ""

# Check Flask installation
if ! python3 -c "import flask" 2>/dev/null; then
    echo " Flask not found. Attempting to install..."
    pip install Flask --break-system-packages -q
    if python3 -c "import flask" 2>/dev/null; then
        echo " Flask installed successfully"
    else
        echo "Failed to install Flask"
        exit 1
    fi
fi

echo " Flask is installed"
echo ""

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo " app.py not found. Make sure you're in the correct directory."
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo " Starting Application..."
echo "════════════════════════════════════════════════════════════"
echo ""
echo " Access the application at:"
echo "    Form Page:      http://localhost:5000/"
echo "    Dashboard:      http://localhost:5000/dashboard"
echo ""
echo "Press Ctrl+C to stop the server"
echo "════════════════════════════════════════════════════════════"
echo ""

# Run the application
python3 app.py
