# Smart Configuration Guide

## 🎯 Problem Solved

**Before:** Had to manually edit `config.py` every time you wanted to switch modes (penny stock, HVB, etc.)

**Now:** Zero code changes needed! Just use CLI flags or profiles.

---

## 🚀 Quick Start

### Method 1: CLI Flags (Easiest)

```bash
# Penny stock mode - auto-configures everything!
python main.py scan --mode swing --penny-stock

# HVB mode - auto-configures everything!
python main.py scan --mode swing --hvb

# Normal mode (default)
python main.py scan --mode swing
```

**What happens:**
- `--penny-stock` automatically:
  - Sets `SYMBOL_SOURCE = 'nifty_smallcap250'`
  - Sets `MIN_CONVICTION_SCORE = 50.0`
  - Sets `PENNY_STOCK_MODE_ENABLED = True`
  - Sets `MIN_AVG_VOLUME = 10000`
  - **No code changes needed!**

- `--hvb` automatically:
  - Sets `HVB_ENABLED = True`
  - Sets `MIN_CONVICTION_SCORE = 70.0`
  - **No code changes needed!**

---

### Method 2: Preset Profiles

```bash
# Use a preset profile
python main.py scan --mode swing --profile penny_stock
python main.py scan --mode swing --profile hvb
python main.py scan --mode swing --profile aggressive
python main.py scan --mode swing --profile conservative
```

**Available Profiles:**
- `normal` - Default settings (NIFTY50, 60% conviction)
- `penny_stock` - Optimized for penny stocks (smallcap250, 50% conviction)
- `hvb` - High volatility breakout mode (70% conviction)
- `aggressive` - More picks, lower threshold (NIFTY200, 55% conviction, HVB enabled)
- `conservative` - Fewer picks, higher quality (NIFTY50, 75% conviction)

---

### Method 3: Environment Variables

Set environment variables to override any config value:

```bash
# Set symbol source
export STOCK_SYMBOL_SOURCE=nifty_smallcap250

# Set conviction threshold
export STOCK_MIN_CONVICTION_SCORE=50.0

# Enable penny stock mode
export STOCK_PENNY_STOCK_MODE_ENABLED=true

# Then run normally
python main.py scan --mode swing
```

**Format:** `STOCK_<CONFIG_KEY>` (uppercase)

**Examples:**
- `STOCK_SYMBOL_SOURCE=nifty200`
- `STOCK_MIN_CONVICTION_SCORE=55.0`
- `STOCK_HVB_ENABLED=true`
- `STOCK_PENNY_STOCK_MODE_ENABLED=true`
- `STOCK_MAX_RISK_PER_TRADE=0.03`

---

## 📋 Profile Details

### Normal Profile
```python
SYMBOL_SOURCE: 'nifty50'
MIN_CONVICTION_SCORE: 60.0
PENNY_STOCK_MODE_ENABLED: False
HVB_ENABLED: False
```

### Penny Stock Profile
```python
SYMBOL_SOURCE: 'nifty_smallcap250'
MIN_CONVICTION_SCORE: 50.0
PENNY_STOCK_MODE_ENABLED: True
HVB_ENABLED: False
MIN_AVG_VOLUME: 10000
```

### HVB Profile
```python
SYMBOL_SOURCE: 'nifty50'
MIN_CONVICTION_SCORE: 70.0
PENNY_STOCK_MODE_ENABLED: False
HVB_ENABLED: True
```

### Aggressive Profile
```python
SYMBOL_SOURCE: 'nifty200'
MIN_CONVICTION_SCORE: 55.0
PENNY_STOCK_MODE_ENABLED: False
HVB_ENABLED: True
```

### Conservative Profile
```python
SYMBOL_SOURCE: 'nifty50'
MIN_CONVICTION_SCORE: 75.0
PENNY_STOCK_MODE_ENABLED: False
HVB_ENABLED: False
```

---

## 🔧 Priority Order

Configuration is applied in this order (later overrides earlier):

1. **Base Config** (`config.py` defaults)
2. **Profile** (if `--profile` specified)
3. **CLI Flags** (`--penny-stock`, `--hvb`)
4. **Environment Variables** (`STOCK_*`)
5. **Explicit Overrides** (programmatic)

**Example:**
```bash
# This will use penny_stock profile, but CLI flag overrides
python main.py scan --profile normal --penny-stock
# Result: Penny stock mode enabled (CLI flag wins)
```

---

## 💡 Real-World Examples

### Example 1: Daily Penny Stock Scan
```bash
# Just add --penny-stock flag - that's it!
python main.py scan --mode swing --penny-stock
```

### Example 2: Aggressive Trading Session
```bash
# Use aggressive profile
python main.py scan --mode intraday --profile aggressive
```

### Example 3: Custom Configuration via Env
```bash
# Set custom threshold via environment
export STOCK_MIN_CONVICTION_SCORE=45.0
python main.py scan --mode swing --penny-stock
# Uses penny stock mode + custom 45% threshold
```

### Example 4: Production vs Testing
```bash
# Production: Conservative
python main.py scan --mode swing --profile conservative

# Testing: Aggressive with more picks
python main.py scan --mode swing --profile aggressive
```

---

## 🎯 Best Practices (Senior Trader Approach)

### 1. **Use Profiles for Consistency**
```bash
# Morning routine: Conservative scan
python main.py scan --mode swing --profile conservative

# Afternoon: More opportunities
python main.py scan --mode swing --profile normal
```

### 2. **Use Flags for Quick Mode Switching**
```bash
# Quick penny stock check
python main.py scan --mode swing --penny-stock

# Quick HVB check
python main.py scan --mode swing --hvb
```

### 3. **Use Environment Variables for Persistent Settings**
```bash
# In your shell profile (~/.bashrc or ~/.zshrc)
export STOCK_MIN_CONVICTION_SCORE=65.0
export STOCK_MAX_RISK_PER_TRADE=0.015

# Now all scans use these defaults
python main.py scan --mode swing
```

### 4. **Create Aliases for Common Commands**
```bash
# In ~/.bashrc or ~/.zshrc
alias stock-scan="python /path/to/main.py scan --mode swing"
alias stock-penny="python /path/to/main.py scan --mode swing --penny-stock"
alias stock-hvb="python /path/to/main.py scan --mode swing --hvb"
alias stock-conservative="python /path/to/main.py scan --mode swing --profile conservative"

# Then just run:
stock-scan
stock-penny
stock-hvb
```

---

## 🔍 How It Works

### Architecture

```
CLI Command
    ↓
ConfigManager.create_config()
    ↓
1. Load base Config (from config.py)
    ↓
2. Apply profile (if --profile specified)
    ↓
3. Apply CLI flags (--penny-stock, --hvb)
    ↓
4. Apply environment variables (STOCK_*)
    ↓
5. Apply explicit overrides (if any)
    ↓
Final Config → Scanner Engine
```

### Code Flow

1. **User runs:** `python main.py scan --penny-stock`
2. **main.py:** Calls `cmd_scan(args, config)`
3. **cmd_scan:** Detects `--penny-stock` flag
4. **ConfigManager:** Creates new config with penny stock settings
5. **Scanner:** Uses the auto-configured config
6. **Result:** No code changes needed!

---

## 📝 Adding Custom Profiles

Edit `config_manager.py` to add your own profiles:

```python
PRESET_PROFILES = {
    'my_custom': {
        'SYMBOL_SOURCE': 'nifty100',
        'MIN_CONVICTION_SCORE': 65.0,
        'HVB_ENABLED': True,
        # ... other settings
    }
}
```

Then use it:
```bash
python main.py scan --profile my_custom
```

---

## ✅ Benefits

1. **Zero Code Changes** - Switch modes without editing files
2. **Consistent** - Profiles ensure same settings every time
3. **Flexible** - Environment variables for fine-tuning
4. **Fast** - CLI flags for quick mode switching
5. **Professional** - Matches how senior traders work

---

## 🎓 Senior Architect & Trader Approach

**Senior Architect would:**
- ✅ Separate configuration from code
- ✅ Support multiple configuration methods
- ✅ Use environment variables for deployment
- ✅ Create reusable profiles
- ✅ Auto-configure based on context

**Senior Trader would:**
- ✅ Quick mode switching (CLI flags)
- ✅ Consistent setups (profiles)
- ✅ No manual config editing
- ✅ Easy to remember commands
- ✅ Fast iteration

**This implementation provides both!** 🎯

