#!/bin/bash
# Daily Stock Scans Runner
# Creates venv if needed, installs requirements, and runs both daily scan scripts

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
SCRIPTS_DIR="scripts"

echo "======================================================================"
echo "📊 DAILY STOCK SCANS - Setup and Execution"
echo "======================================================================"
echo ""

# Check LLM configuration
LLM_ENABLED="${STOCK_LLM_ENABLED:-true}"
HAS_OPENAI_KEY=false
HAS_ANTHROPIC_KEY=false

if [ -n "$STOCK_OPENAI_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    HAS_OPENAI_KEY=true
fi

if [ -n "$STOCK_ANTHROPIC_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
    HAS_ANTHROPIC_KEY=true
fi

# Auto-detect provider if not explicitly set
if [ -z "$STOCK_LLM_PROVIDER" ]; then
    if [ "$HAS_ANTHROPIC_KEY" = "true" ]; then
        export STOCK_LLM_PROVIDER="anthropic"
        LLM_PROVIDER="anthropic"
        # Set default Anthropic model if not specified
        if [ -z "$STOCK_LLM_MODEL" ]; then
            export STOCK_LLM_MODEL="claude-3-haiku-20240307"
        fi
    elif [ "$HAS_OPENAI_KEY" = "true" ]; then
        export STOCK_LLM_PROVIDER="openai"
        LLM_PROVIDER="openai"
    else
        LLM_PROVIDER="${STOCK_LLM_PROVIDER:-openai}"
    fi
else
    LLM_PROVIDER="$STOCK_LLM_PROVIDER"
    # Set appropriate default model if provider is set but model is not
    if [ -z "$STOCK_LLM_MODEL" ]; then
        if [ "$LLM_PROVIDER" = "anthropic" ]; then
            export STOCK_LLM_MODEL="claude-3-haiku-20240307"
        fi
    fi
fi

# Display LLM status
if [ "$LLM_ENABLED" = "true" ] || [ "$LLM_ENABLED" = "True" ] || [ "$LLM_ENABLED" = "1" ]; then
    if [ "$LLM_PROVIDER" = "openai" ] && [ "$HAS_OPENAI_KEY" = "true" ]; then
        echo "🤖 LLM: ENABLED (OpenAI) - Auto-detected from API key"
    elif [ "$LLM_PROVIDER" = "anthropic" ] && [ "$HAS_ANTHROPIC_KEY" = "true" ]; then
        echo "🤖 LLM: ENABLED (Anthropic) - Auto-detected from API key"
    elif [ "$LLM_PROVIDER" = "local" ] || [ "$LLM_PROVIDER" = "ollama" ]; then
        echo "🤖 LLM: ENABLED (Local/Ollama)"
    else
        echo "🤖 LLM: CONFIGURED but API key not found - will use keyword-based methods"
        if [ "$LLM_PROVIDER" = "openai" ]; then
            echo "   💡 Set STOCK_OPENAI_API_KEY to enable LLM features"
        elif [ "$LLM_PROVIDER" = "anthropic" ]; then
            echo "   💡 Set STOCK_ANTHROPIC_API_KEY to enable LLM features"
        else
            echo "   💡 Set STOCK_OPENAI_API_KEY or STOCK_ANTHROPIC_API_KEY to enable LLM features"
        fi
    fi
else
    echo "🤖 LLM: DISABLED (using keyword-based methods)"
fi
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
    echo ""
    
    # Show LLM status in summary
    if [ "$LLM_ENABLED" = "true" ] || [ "$LLM_ENABLED" = "True" ] || [ "$LLM_ENABLED" = "1" ]; then
        if [ "$LLM_PROVIDER" = "openai" ] && [ "$HAS_OPENAI_KEY" = "true" ]; then
            echo "🤖 LLM-enhanced analysis was used for insights (OpenAI)"
        elif [ "$LLM_PROVIDER" = "anthropic" ] && [ "$HAS_ANTHROPIC_KEY" = "true" ]; then
            echo "🤖 LLM-enhanced analysis was used for insights (Anthropic)"
        elif [ "$LLM_PROVIDER" = "local" ] || [ "$LLM_PROVIDER" = "ollama" ]; then
            echo "🤖 LLM-enhanced analysis was used (local model)"
        else
            echo "💡 Tip: Set STOCK_OPENAI_API_KEY or STOCK_ANTHROPIC_API_KEY to enable LLM-enhanced analysis"
        fi
    fi
    
    exit 0
else
    echo "⚠️  One or more scans had issues"
    echo "   Stocks exit code: $STOCKS_EXIT_CODE"
    echo "   Penny stocks exit code: $PENNY_EXIT_CODE"
    exit 1
fi

