# Project Structure

This document describes the reorganized project structure.

## Directory Layout

```
ai_stock_discovery_tool/
├── stock_discovery/          # Core package (all Python modules)
│   ├── __init__.py
│   ├── config.py
│   ├── config_manager.py
│   ├── database.py
│   ├── data_fetcher.py
│   ├── fundamental_analyzer.py
│   ├── learning.py
│   ├── market_context.py
│   ├── multi_timeframe.py
│   ├── news_fetcher.py
│   ├── output_formatter.py
│   ├── risk_manager.py
│   ├── scanner_engine.py
│   ├── scheduler.py
│   ├── scoring_engine.py
│   ├── symbol_loader.py
│   ├── technical_indicators.py
│   ├── backtesting.py
│   └── strategies/           # Trading strategies
│       ├── __init__.py
│       ├── orb_strategy.py
│       ├── vwap_strategy.py
│       ├── momentum_strategy.py
│       ├── hvb_strategy.py
│       └── earnings_strategy.py
│
├── scripts/                  # Entry point scripts
│   ├── main.py              # Main CLI tool
│   ├── daily_stocks.py      # Daily regular stocks scan
│   └── daily_penny_stocks.py # Daily penny stocks scan
│
├── docs/                     # All documentation
│   ├── README.md
│   ├── AI_Mac_Stock_Discovery_Tool_PRD.md
│   ├── AUDIT_REPORT.md
│   └── ... (other .md files)
│
├── data/                     # Data files
│   ├── picks_ledger.db       # SQLite database
│   ├── symbols_cache.pkl     # Symbol cache
│   └── symbols_example.csv  # Example CSV
│
├── tests/                     # Test files
│   ├── test_build.py
│   └── test_components.py
│
├── daily_picks/              # Output directory (generated)
│   └── YYYY-MM-DD/          # Daily folders
│       ├── today_stocks.txt
│       ├── today_stocks.json
│       ├── today_penny_stocks.txt
│       └── today_penny_stocks.json
│
├── venv/                     # Virtual environment (not in git)
├── requirements.txt          # Python dependencies
└── run_daily_scans.sh        # Shell script to run daily scans
```

## Usage

### Running the Main Tool

```bash
# From project root
python scripts/main.py scan --mode intraday
python scripts/main.py scan --mode swing --hvb
```

### Running Daily Scripts

```bash
# Individual scripts
python scripts/daily_stocks.py
python scripts/daily_penny_stocks.py

# Or use the shell script (handles venv setup)
./run_daily_scans.sh
```

### Importing the Package

```python
from stock_discovery.config import Config
from stock_discovery.scanner_engine import ScannerEngine
from stock_discovery.database import PickLedger
```

## Key Changes from Previous Structure

1. **Core modules** moved to `stock_discovery/` package
2. **Scripts** moved to `scripts/` directory
3. **Documentation** consolidated in `docs/`
4. **Data files** moved to `data/`
5. **Tests** moved to `tests/`
6. **All imports** updated to use `stock_discovery.*` package
7. **File paths** updated to reference new locations

## Backward Compatibility

- Database path: Automatically uses `data/picks_ledger.db` if available, falls back to root
- Symbol cache: Automatically uses `data/symbols_cache.pkl` if available, falls back to root
- CSV files: Automatically checks `data/` directory if not found in root

