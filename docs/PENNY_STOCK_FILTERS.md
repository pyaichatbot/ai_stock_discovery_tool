# Penny Stock Filters - Implementation Status

## ✅ Implemented Filters

### 1. **Pump/Dump Filter** ✅
- **Status**: Implemented
- **Location**: `stock_discovery/scanner_engine.py` (lines ~157-168)
- **Logic**: 
  - Detects extreme gap-ups (>20% for penny stocks, >15% for normal)
  - Filters out if spike occurs on thin volume (relative volume < 1.5)
  - Prevents classic pump profiles

### 2. **Price History Filter** ✅
- **Status**: Implemented
- **Location**: `stock_discovery/scanner_engine.py` (line ~150)
- **Logic**:
  - Penny stocks: Require at least 90 days (3-6 months) of price history
  - Normal stocks: Require at least 20 days (1 month)
  - Filters out stocks with insufficient data (avoids shells)

### 3. **Revenue Check** ✅
- **Status**: Implemented
- **Location**: `stock_discovery/scanner_engine.py` (lines ~200-203)
- **Logic**:
  - For penny stocks: Checks for non-zero revenue
  - Filters out companies with zero or negative revenue (possible shell companies)

### 4. **Relative Volume Filter** ✅
- **Status**: Implemented
- **Location**: `stock_discovery/scanner_engine.py` (lines ~178-182)
- **Logic**:
  - For penny stock intraday entries: Requires relative volume >= 2.0
  - Relative volume = today's volume / 20-day average volume
  - Ensures sufficient liquidity for execution

### 5. **Circuit Breaker Check** ✅
- **Status**: Already implemented
- **Location**: `stock_discovery/scanner_engine.py` (line ~174)
- **Logic**: Skips stocks in trading halt

## ⚠️ Partially Implemented / Needs Data Source

### 6. **ASM/GSM Surveillance Check** ⚠️
- **Status**: Placeholder added, needs data source integration
- **Location**: `stock_discovery/scanner_engine.py` (lines ~185-189)
- **Note**: 
  - Requires external NSE/BSE API for real-time ASM/GSM status
  - Currently relies on circuit breaker checks which catch some cases
  - TODO: Integrate ASM/GSM data source when available

## 📊 Configuration Parameters

### Current Penny Stock Configuration (Perplexity-optimized)

```python
# Price band
PENNY_STOCK_MIN_PRICE = 1.0
PENNY_STOCK_MAX_PRICE = 50.0

# Quality & signal strength
MIN_CONVICTION_SCORE = 55.0  # Target 0-3 picks/day

# Liquidity
MIN_AVG_VOLUME = 150,000  # Tighter requirement

# Volatility constraints
MAX_VOLATILITY_PERCENTILE = 92.0  # Prevent extremes

# Portfolio / concurrency
MAX_CONCURRENT_POSITIONS = 5
```

### Additional Filters Applied

- **Relative Volume**: >= 2.0x for intraday entries
- **Price History**: >= 90 days for penny stocks
- **Pump Filter**: Blocks >20% spikes on thin volume
- **Revenue Check**: Non-zero revenue required

## 🔧 Tuning Guide

### If you see too many candidates:
- Raise `MIN_CONVICTION_SCORE` toward 60-65
- Increase `MIN_AVG_VOLUME` toward 300k+
- Tighten `MAX_VOLATILITY_PERCENTILE` to 90.0

### If you see almost none on most days:
- Loosen `MIN_CONVICTION_SCORE` in steps of 5
- Widen volatility cap slightly (e.g., 95th percentile)
- Lower `MIN_AVG_VOLUME` (but keep >= 100k for liquidity)

## 📝 Notes

1. **ASM/GSM Integration**: Currently not implemented due to lack of data source. Would require NSE/BSE API integration.

2. **Relative Volume**: The 2.0x requirement for intraday entries is strict but necessary for penny stocks to ensure execution quality.

3. **Pump Filter**: The 20% threshold for penny stocks is appropriate as they're more volatile, but we still filter out thin-volume spikes.

4. **Revenue Check**: Only applies to penny stocks to avoid shell companies while being lenient on other fundamental metrics.

