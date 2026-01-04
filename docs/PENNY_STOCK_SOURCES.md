# Penny Stock Symbol Sources

## Overview

This document explains where and how to access penny stock symbols (stocks priced ₹1-50) for the AI Stock Discovery Tool.

---

## 🎯 Available Symbol Sources

### 1. **NSE Smallcap Indices** (Recommended)

**NIFTY Smallcap 100 & 250** - Official NSE indices containing small-cap stocks, many of which are penny stocks.

#### Usage:
```python
# In config.py
SYMBOL_SOURCE: str = 'nifty_smallcap100'  # 100 stocks
# OR
SYMBOL_SOURCE: str = 'nifty_smallcap250'  # 250 stocks (more options)
```

#### Advantages:
- ✅ Official NSE data (reliable, up-to-date)
- ✅ Automatically fetched via API
- ✅ Contains many stocks in ₹1-50 range
- ✅ Cached for performance

#### How it works:
- Fetches from NSE API: `https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20SMALLCAP%20100`
- Falls back to hardcoded list if API fails
- Symbols cached for 7 days

---

### 2. **Automatic Price Filtering** (Best for Penny Stocks)

Automatically filters stocks by price from a larger index.

#### Usage:
```python
# In config.py
SYMBOL_SOURCE: str = 'penny_stocks'  # Automatically filters by price
PENNY_STOCK_MAX_PRICE: float = 50.0  # Max price threshold
```

#### How it works:
- Loads NIFTY Smallcap 250 (or other source)
- Fetches current price for each stock
- Filters stocks priced ≤ ₹50
- Returns only penny stocks

#### Advantages:
- ✅ Guaranteed to return only penny stocks
- ✅ No manual curation needed
- ✅ Updates automatically as prices change

#### Note:
- First run may take 2-5 minutes (fetching prices for all stocks)
- Results are cached for performance

---

### 3. **CSV File** (Manual Curation)

Create your own CSV file with penny stock symbols.

#### Usage:
```python
# In config.py
SYMBOL_SOURCE: str = 'csv'
SYMBOL_CSV_PATH: str = 'penny_stocks.csv'
```

#### CSV Format:
```csv
symbol
YESBANK.NS
IDEA.NS
RCOM.NS
SUZLON.NS
JAIPRAKASH.NS
```

#### Where to get symbols:
- **NSE Website**: https://www.nseindia.com/market-data/equity-derivatives
- **BSE Website**: https://www.bseindia.com/markets/equity/EQReports/StockPrcHistori.aspx
- **Financial Websites**:
  - Bajaj Finserv: Lists of penny stocks
  - 5paisa: Penny stock lists
  - Ventura Securities: Curated penny stocks
  - INDmoney: Stock screener (filter by price < ₹50)

#### Advantages:
- ✅ Full control over symbol list
- ✅ Can include BSE stocks (use `.BO` suffix)
- ✅ Can include specific sectors/themes

---

### 4. **NSE API Direct Access**

Access NSE indices directly via API.

#### Available Indices:
- `NIFTY 50` - Large cap
- `NIFTY 100` - Large + Mid cap
- `NIFTY 200` - Large + Mid cap
- `NIFTY 500` - Broad market
- `NIFTY SMALLCAP 100` - Small cap (many penny stocks)
- `NIFTY SMALLCAP 250` - More small cap stocks
- `NIFTY MIDCAP 150` - Mid cap stocks

#### API Endpoint:
```
https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20SMALLCAP%20100
```

#### Example Code:
```python
from symbol_loader import SymbolLoader

loader = SymbolLoader()
symbols = loader.get_symbols('nifty_smallcap100', refresh=True)
print(f"Loaded {len(symbols)} symbols")
```

---

## 📊 Recommended Setup for Penny Stocks

### Option 1: Automatic (Easiest)
```python
# config.py
SYMBOL_SOURCE: str = 'penny_stocks'
PENNY_STOCK_MAX_PRICE: float = 50.0
```

### Option 2: NSE Smallcap Index
```python
# config.py
SYMBOL_SOURCE: str = 'nifty_smallcap250'  # Larger universe
```

### Option 3: Custom CSV
```python
# config.py
SYMBOL_SOURCE: str = 'csv'
SYMBOL_CSV_PATH: str = 'my_penny_stocks.csv'
```

---

## 🔍 Finding Penny Stocks Manually

### Method 1: NSE Website
1. Go to: https://www.nseindia.com/market-data/equity-derivatives
2. Filter by price range: ₹1 - ₹50
3. Export or manually copy symbols
4. Add `.NS` suffix (e.g., `YESBANK.NS`)

### Method 2: BSE Website
1. Go to: https://www.bseindia.com/markets/equity/EQReports/StockPrcHistori.aspx
2. Filter by price
3. Add `.BO` suffix for BSE stocks

### Method 3: Financial Data Providers
- **Yahoo Finance**: Search for stocks, filter by price
- **Moneycontrol**: Stock screener with price filters
- **Screener.in**: Advanced stock screening (free)

### Method 4: Broker Platforms
- **Zerodha Kite**: Market watchlists, filter by price
- **Upstox**: Stock screener
- **Groww**: Stock discovery with filters

---

## ⚙️ Configuration Examples

### Example 1: Smallcap 100
```python
SYMBOL_SOURCE: str = 'nifty_smallcap100'
PENNY_STOCK_MODE_ENABLED: bool = True
```

### Example 2: Price-Filtered Penny Stocks
```python
SYMBOL_SOURCE: str = 'penny_stocks'
PENNY_STOCK_MAX_PRICE: float = 50.0
PENNY_STOCK_MIN_PRICE: float = 1.0
```

### Example 3: Custom List
```python
SYMBOL_SOURCE: str = 'csv'
SYMBOL_CSV_PATH: str = 'penny_stocks.csv'
```

---

## 🚀 Quick Start

1. **Enable penny stock mode**:
   ```python
   PENNY_STOCK_MODE_ENABLED: bool = True
   ```

2. **Set symbol source**:
   ```python
   SYMBOL_SOURCE: str = 'nifty_smallcap250'  # or 'penny_stocks'
   ```

3. **Run scan**:
   ```bash
   python main.py scan --mode swing --penny-stock
   ```

---

## 📝 Notes

- **NIFTY50/100/200** typically don't contain penny stocks (mostly large-cap)
- **NIFTY Smallcap 100/250** contain many penny stocks
- **Price filtering** (`penny_stocks` source) guarantees penny stocks
- **CSV** gives you full control but requires manual maintenance
- All sources support caching for performance

---

## 🔗 Useful Links

- **NSE Indices**: https://www.nseindia.com/market-data/indices
- **NSE API Docs**: https://www.nseindia.com/api
- **BSE Indices**: https://www.bseindia.com/markets/indices/indiceswatch.aspx
- **Stock Screeners**:
  - Screener.in: https://www.screener.in
  - Moneycontrol: https://www.moneycontrol.com/stockscreener

---

## ⚠️ Important Warnings

1. **Penny stocks are HIGH RISK** - Use with extreme caution
2. **Low liquidity** - May have wide bid-ask spreads
3. **High volatility** - Can move 10-20% in a day
4. **Manipulation risk** - Easier to manipulate than large-cap stocks
5. **Circuit breakers** - More likely to hit upper/lower circuits

Always do your own research before investing!

