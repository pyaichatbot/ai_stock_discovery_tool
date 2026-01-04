#!/bin/bash
# Daily Stock Scans Runner
# Creates venv if needed, installs requirements, and runs both daily scan scripts

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
SCRIPTS_DIR="scripts"

echo "======================================================================"
echo "📊 DAILY STOCK SCANS - Setup and Execution"
echo "======================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo ""

# Install/upgrade requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "📦 Installing/upgrading requirements..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "$REQUIREMENTS_FILE"
    echo "✅ Requirements installed"
else
    echo "⚠️  Warning: $REQUIREMENTS_FILE not found, skipping requirements installation"
fi

echo ""
echo "======================================================================"
echo "🚀 Running Daily Scans"
echo "======================================================================"
echo ""

# Run daily stocks script
echo "📈 Running daily_stocks.py..."
echo "----------------------------------------------------------------------"
python scripts/daily_stocks.py
STOCKS_EXIT_CODE=$?

echo ""
echo "----------------------------------------------------------------------"
if [ $STOCKS_EXIT_CODE -eq 0 ]; then
    echo "✅ Daily stocks scan completed"
else
    echo "⚠️  Daily stocks scan exited with code $STOCKS_EXIT_CODE"
fi

echo ""
echo ""

# Run daily penny stocks script
echo "💰 Running daily_penny_stocks.py..."
echo "----------------------------------------------------------------------"
python scripts/daily_penny_stocks.py
PENNY_EXIT_CODE=$?

echo ""
echo "----------------------------------------------------------------------"
if [ $PENNY_EXIT_CODE -eq 0 ]; then
    echo "✅ Daily penny stocks scan completed"
else
    echo "⚠️  Daily penny stocks scan exited with code $PENNY_EXIT_CODE"
fi

echo ""
echo "======================================================================"
echo "📊 Summary"
echo "======================================================================"
echo ""

if [ $STOCKS_EXIT_CODE -eq 0 ] && [ $PENNY_EXIT_CODE -eq 0 ]; then
    echo "✅ Both scans completed successfully"
    echo ""
    echo "📁 Output files saved in: daily_picks/$(date +%Y-%m-%d)/"
    exit 0
else
    echo "⚠️  One or more scans had issues"
    echo "   Stocks exit code: $STOCKS_EXIT_CODE"
    echo "   Penny stocks exit code: $PENNY_EXIT_CODE"
    exit 1
fi

