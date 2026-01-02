# AI-Powered Stock Discovery Tool

**Version 1.0** - Complete with Learning Loop (Phase 1+2+3)

Mac-only stock discovery system with AI-assisted analysis and feedback learning.

## Features

✅ **Automated Market Scanning** - Scans NIFTY stocks for opportunities  
✅ **4 Core Strategies** - ORB, VWAP Pullback, Momentum Swing, High Volatility Breakout  
✅ **Learning from Feedback** - Adapts based on your outcomes and preferences  
✅ **Risk Management** - Position sizing, stop-loss, targets  
✅ **Pick History** - Complete ledger of all picks and outcomes  

## Installation

### Prerequisites
- Python 3.11+ (recommended)
- macOS (tested on Apple Silicon and Intel)

### Setup

```bash
# Clone or download the code
cd stock_discovery

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Run Market Scan

```bash
# Intraday scan (default)
python main.py scan --mode intraday

# Swing trading scan
python main.py scan --mode swing

# Enable HIGH RISK HVB mode (opt-in)
python main.py scan --mode intraday --hvb
```

**Output Example:**
```
======================================================================
📊 TOP 3 STOCKS - Dec 30, 2024
======================================================================

1. RELIANCE - ORB
   Conviction: 82.5/100 | Risk: Medium Risk
   Entry: ₹2955.00 | SL: ₹2920.00 | Target: ₹3010.00
   Position Size: €286 (100 shares)
   Risk/Reward: 1:1.57
   Setup: Breakout above opening range with strong volume
   🧠 Learning Adjustments:
      • Strategy weight: +3.2 (ORB performance in bullish)
      Original score: 79.3 → Adjusted: 82.5 (+3.2)
```

### 2. Provide Feedback

After executing or reviewing picks, provide feedback:

```bash
# If you took the trade
python main.py feedback \
  --pick-id RELIANCE_20241230_0930 \
  --took yes \
  --rating 4 \
  --note "Entry was clean, hit first target"

# If you rejected the trade
python main.py feedback \
  --pick-id TCS_20241230_0945 \
  --took no \
  --rating 2 \
  --reject-reason "too_risky" \
  --note "Volume was suspicious"
```

### 3. Compute Outcomes (Daily)

Run this after market close to update learning:

```bash
python main.py compute-outcomes
```

This will:
- Calculate MFE/MAE for all pending picks
- Update strategy performance stats
- Adjust feature penalties
- Recalculate strategy weights

### 4. Review Performance

```bash
# Weekly review
python main.py review --period week

# Monthly review
python main.py review --period month
```

## Configuration

Edit `config.py` to customize:

```python
# Trading Parameters
TOTAL_BUDGET: float = 500.0  # Your trading capital
MAX_RISK_PER_TRADE: float = 0.02  # 2% risk per trade
MIN_CONVICTION_SCORE: float = 75.0  # Minimum score to generate pick

# Symbol Source (NEW!)
SYMBOL_SOURCE: str = 'nifty50'  # Options: 'nifty50', 'nifty100', 'nifty200', 
                                 # 'zerodha_popular', 'csv', 'manual'
SYMBOL_CSV_PATH: str = 'symbols.csv'  # Used if SYMBOL_SOURCE = 'csv'

# Market Filters
MIN_AVG_VOLUME: int = 100000  # Minimum liquidity
MIN_PRICE: float = 50.0
MAX_PRICE: float = 5000.0

# HVB Mode
HVB_ENABLED: bool = False  # Set to True to allow HVB picks
```

### Symbol Source Options

**Built-in indices:**
- `'nifty50'` - Top 50 stocks (fastest, recommended for beginners)
- `'nifty100'` - Top 100 stocks (balanced)
- `'nifty200'` - Top 200 stocks (comprehensive)

**Curated lists:**
- `'zerodha_popular'` - ~70 high-liquidity stocks commonly traded

**Custom:**
- `'csv'` - Load from your own CSV file (see `symbols_example.csv`)
- `'manual'` - Use hardcoded fallback

📖 **See `SYMBOL_LOADING.md` for detailed guide on dynamic symbol loading**

## Learning System

### How It Works

1. **Baseline Phase** (0-10 picks)
   - Collects data, no adjustments

2. **Conservative Learning** (10-50 picks)
   - ±5% weight adjustments
   - Identifies obvious patterns

3. **Full Learning** (50+ picks)
   - ±20% weight adjustments
   - Advanced pattern recognition

### What Gets Learned

- **Strategy Performance by Regime** - Which strategies work best in bullish/bearish/neutral markets
- **Feature Penalties** - Patterns that consistently fail (e.g., gaps without volume)
- **Personal Preferences** - What you tend to accept/reject

### Transparency

All learning adjustments are shown in pick output:
```
🧠 Learning Adjustments:
   • Strategy weight: +4.5 (MOMENTUM_SWING performance in bullish)
   • Penalty: -2.0 (gap without volume)
   Original score: 78.0 → Adjusted: 80.5 (+2.5)
```

## Strategies

### 1. Opening Range Breakout (ORB)
- **Risk**: Medium
- **Timeframe**: Intraday (1-15 min)
- **Logic**: Breakout above first 15-min range with volume

### 2. VWAP Pullback
- **Risk**: Medium
- **Timeframe**: Intraday
- **Logic**: Price pulls back to VWAP in uptrend

### 3. Momentum Swing
- **Risk**: Medium
- **Timeframe**: Daily (2-30 days)
- **Logic**: MA crossover + RSI + volume confirmation

### 4. High Volatility Breakout (HVB)
- **Risk**: ⚠️ HIGH RISK
- **Timeframe**: Daily
- **Logic**: Extreme volatility + breakout + volume surge
- **Note**: Opt-in only, max 1 pick per day

## Database

All data stored in `picks_ledger.db` (SQLite):

**Tables:**
- `picks` - All generated picks
- `feedback` - Your manual feedback
- `outcomes` - Computed results (MFE/MAE/returns)
- `strategy_stats` - Performance by strategy/regime
- `feature_penalties` - Learned pattern penalties

**Backup:**
```bash
cp picks_ledger.db picks_ledger_backup_$(date +%Y%m%d).db
```

## Safety & Disclaimers

⚠️ **IMPORTANT**:
- This is a **research tool only**
- No auto-trading or order placement
- No guarantee of returns
- Markets involve substantial risk
- You are responsible for all trading decisions

## Troubleshooting

### No picks generated
- Check market regime (bearish markets = fewer setups)
- Lower `MIN_CONVICTION_SCORE` in config
- Check if stocks meet filters (price, volume)

### Data fetch errors
- Check internet connection
- yfinance may have rate limits
- NSE stocks use `.NS` suffix (e.g., `RELIANCE.NS`)

### Learning not working
- Need minimum 10 picks before adjustments start
- Run `compute-outcomes` after market close
- Check `strategy_stats` table in database

## Workflow

**Daily Routine:**

1. **Pre-market** (9:00 AM)
   ```bash
   python main.py scan --mode intraday
   ```

2. **Review picks** - Decide which to execute

3. **Execute trades** - Manual entry on broker platform

4. **End of day** (3:30 PM)
   ```bash
   # Add feedback for each pick
   python main.py feedback --pick-id <id> --took yes --rating 4
   
   # Compute outcomes
   python main.py compute-outcomes
   ```

5. **Weekly review** (Friday)
   ```bash
   python main.py review --period week
   ```

## Files Structure

```
stock_discovery/
├── main.py                    # Entry point
├── config.py                  # Configuration
├── database.py                # SQLite operations
├── data_fetcher.py            # Market data
├── technical_indicators.py    # TA calculations
├── learning.py                # Feedback learning
├── scanner_engine.py          # Main orchestrator
├── output_formatter.py        # Display formatting
├── strategies/
│   ├── orb_strategy.py       # Opening Range Breakout
│   ├── vwap_strategy.py      # VWAP Pullback
│   ├── momentum_strategy.py  # Momentum Swing
│   └── hvb_strategy.py       # High Volatility Breakout
├── requirements.txt           # Dependencies
└── picks_ledger.db           # Database (created on first run)
```

## Future Enhancements

- [ ] Web dashboard (FastAPI)
- [ ] More strategies (earnings drift, gap fill)
- [ ] Multi-timeframe analysis
- [ ] News sentiment integration
- [ ] Broker integration (read-only)
- [ ] Performance metrics dashboard

## Support

For issues or questions:
1. Check logs for error details
2. Verify config settings
3. Test with `--mode swing` (less data dependency)

---

**Version**: 1.0  
**Last Updated**: December 30, 2024  
**License**: Personal Use Only
