# Symbol Loading Explained

## How Symbol Loading Works

The symbol loading system uses a **3-tier approach** with automatic fallback:

---

## 🔄 Loading Flow

```
1. Check Cache (if refresh=False)
   ↓ (if cache exists and valid)
   ✅ Return cached symbols
   
   ↓ (if no cache or refresh=True)
   
2. Try NSE API
   ↓ (if API succeeds)
   ✅ Fetch from NSE → Save to cache → Return symbols
   
   ↓ (if API fails)
   
3. Use Hardcoded Fallback
   ✅ Use pre-defined list → Save to cache → Return symbols
```

---

## 📋 Detailed Explanation

### **Tier 1: Cache (Fastest)**
- **File:** `symbols_cache.pkl`
- **Duration:** 7 days (configurable)
- **When used:** First check if `refresh=False`
- **Benefit:** Fast, no network calls

### **Tier 2: NSE API (Primary Source)**
- **Endpoint:** `https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050`
- **Method:** HTTP GET request with session cookies
- **When used:** If cache missing/expired or `refresh=True`
- **Benefit:** Always up-to-date, official source
- **Fallback:** If API fails → goes to Tier 3

### **Tier 3: Hardcoded List (Fallback)**
- **Location:** Inside `symbol_loader.py` (lines 150-200+)
- **Content:** Pre-defined NIFTY 50/100/200 symbols
- **When used:** Only if NSE API fails
- **Benefit:** Always works, no network dependency
- **Limitation:** May be outdated if NIFTY constituents change

---

## 🎯 Current Status

**Default Behavior:**
- Uses **cache** (if available)
- Cache was created from **NSE API** (when first run)
- Falls back to **hardcoded** only if API fails

**To see which source is used:**
- Check console output:
  - `📦 Loaded X symbols from cache` → Using cache
  - `✅ Fetched X symbols from NSE API` → Using API
  - `⚠️ NSE API failed, using hardcoded list` → Using fallback

---

## ⚙️ Configuration

**In `config.py`:**
```python
SYMBOL_SOURCE: str = 'nifty50'  # Options: nifty50, nifty100, nifty200, csv
REFRESH_SYMBOLS: bool = False    # Set True to force API refresh
```

**Options:**
- `nifty50` → NIFTY 50 stocks
- `nifty100` → NIFTY 100 stocks
- `nifty200` → NIFTY 200 stocks
- `csv` → Load from CSV file (custom symbols)

---

## 🔍 How to Check Current Source

**Method 1: Check cache file**
```bash
ls -lh symbols_cache.pkl
```

**Method 2: Force refresh to see API**
```python
from symbol_loader import SymbolLoader
loader = SymbolLoader()
symbols = loader.get_symbols('nifty50', refresh=True)
# Will show: "✅ Fetched X symbols from NSE API"
```

**Method 3: Check console output**
- When running scan, look for:
  - `📦 Loaded X symbols from cache` → Cache
  - `🔄 Fetching symbols from nifty50...` → API or fallback
  - `✅ Fetched X symbols from NSE API` → API succeeded
  - `⚠️ NSE API failed, using hardcoded list` → Fallback used

---

## 📊 Example Flow

**First Run (No Cache):**
```
1. Check cache → Not found
2. Try NSE API → ✅ Success
3. Save to cache
4. Return 50 symbols from API
```

**Subsequent Runs (Cache Exists):**
```
1. Check cache → ✅ Found (valid)
2. Return 50 symbols from cache
   (No API call needed)
```

**If API Fails:**
```
1. Check cache → Not found or expired
2. Try NSE API → ❌ Failed (network issue)
3. Use hardcoded list → ✅ Success
4. Save to cache
5. Return 50 symbols from hardcoded list
```

---

## 🎯 Summary

**Answer: It's ALL THREE, with priority:**

1. **Cache** (if available) ← Fastest
2. **NSE API** (primary source) ← Most up-to-date
3. **Hardcoded** (fallback) ← Always works

**Current state:** Your symbols are loaded from **cache**, which was originally fetched from **NSE API**.

**To force API refresh:**
```python
# In config.py
REFRESH_SYMBOLS: bool = True

# Or in code
symbols = loader.get_symbols('nifty50', refresh=True)
```

---

## 💡 Why This Design?

1. **Performance:** Cache is fast (no network delay)
2. **Reliability:** Fallback ensures it always works
3. **Freshness:** API provides latest NIFTY constituents
4. **Flexibility:** Can use CSV for custom symbols

**Best of all worlds!** ✅

