# Scanner Engine & Penny Stocks - Review Improvements

## ✅ Implemented Improvements

### 1. **Top-3 Limit Alignment** ✅
- **Issue**: Script sliced to 3, but engine had `PENNY_STOCK_MAX_PICKS = 2`
- **Fix**: Set `config.PENNY_STOCK_MAX_PICKS = 3` in daily script to align with engine
- **Location**: `scripts/daily_penny_stocks.py` (line 204)
- **Result**: Engine enforces 3 picks, script keeps `[:3]` as safety net

### 2. **Risk Reset Logic Improvement** ✅
- **Issue**: Clearing all pending picks destroyed outcome data for traded positions
- **Fix**: Only clear picks older than 7 days (preserves recent trading history)
- **Location**: `scripts/daily_penny_stocks.py` (lines 168-183)
- **Result**: Maintains trading history while preventing position limit issues

### 3. **Config Echo Reduction** ✅
- **Issue**: Both script and engine printed config details (noisy logs)
- **Fix**: 
  - Script prints detailed config (Perplexity-optimized settings)
  - Engine only prints penny-risk warning (once)
- **Location**: 
  - `scripts/daily_penny_stocks.py` (lines 206-212)
  - `stock_discovery/scanner_engine.py` (lines 73-79)
- **Result**: Cleaner logs with config details in script, warnings in engine

### 4. **Error Handling Enhancement** ✅
- **Issue**: Generic exception handler only logged `str(e)`
- **Fix**: Log `type(e).__name__` and `repr(e)` for better debugging
- **Location**: 
  - `scripts/daily_penny_stocks.py` (line 242)
  - `scripts/daily_stocks.py` (line 198)
- **Result**: Better error context in cron logs for debugging

### 5. **Position Sizing Debug Logging** ✅
- **Issue**: No visibility into risk calculations for penny stocks
- **Fix**: Added debug logging for risk_amount, risk_per_share, position_size, stop_pct
- **Location**: `stock_discovery/scanner_engine.py` (lines 347-352)
- **Result**: Helps tune stops and position sizing in production

### 6. **Penny Stock Picks Logic** ✅
- **Issue**: In penny mode, normal picks could mix with penny picks
- **Fix**: For penny stock mode, only return penny picks (not normal picks)
- **Location**: `stock_discovery/scanner_engine.py` (lines 126-135)
- **Result**: Pure penny stock suggestions without mixing

### 7. **Price Cap Consistency** ✅
- **Status**: Already implemented
- **Location**: `stock_discovery/scanner_engine.py` (lines 158-162)
- **Note**: Price filtering happens early in `_analyze_symbol`, ensuring consistent application

## 📊 Configuration Summary

### Daily Penny Stock Script Configuration
```python
PENNY_STOCK_MIN_PRICE = 1.0
PENNY_STOCK_MAX_PRICE = 50.0
MIN_CONVICTION_SCORE = 55.0  # Target 0-3 picks/day
MIN_AVG_VOLUME = 150,000
MAX_VOLATILITY_PERCENTILE = 92.0
MAX_CONCURRENT_POSITIONS = 5
PENNY_STOCK_MAX_PICKS = 3  # Aligned with script's top-3 limit
```

## 🔧 Tuning Recommendations

### If too many candidates:
- Raise `MIN_CONVICTION_SCORE` toward 60-65
- Increase `MIN_AVG_VOLUME` toward 300k+
- Tighten `MAX_VOLATILITY_PERCENTILE` to 90.0

### If almost none on most days:
- Loosen `MIN_CONVICTION_SCORE` in steps of 5
- Widen volatility cap slightly (e.g., 95th percentile)
- Lower `MIN_AVG_VOLUME` (but keep >= 100k for liquidity)

## 📝 Notes

1. **Position Sizing Debug**: Logging only active when `LLM_ENABLED=True` (indicates debug mode)
2. **Risk Reset**: 7-day cutoff preserves recent trading data while clearing old suggestions
3. **Top-3 Alignment**: Engine enforces limit, script keeps safety net for robustness
4. **Error Handling**: `repr(e)` provides full error context including type information

## 🎯 Next Steps

1. **Empirical Tuning**: Monitor daily pick count and realized outcomes
2. **Iterate on Thresholds**: Adjust `MIN_CONVICTION_SCORE`, `MIN_AVG_VOLUME`, `PENNY_STOCK_MAX_PICKS` based on results
3. **ASM/GSM Integration**: When data source available, integrate SEBI surveillance checks
4. **Performance Optimization**: Consider parallelization for large symbol lists (future enhancement)

