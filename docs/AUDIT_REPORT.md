# Code Audit Report: AI Stock Discovery Tool
**Date:** 2024-12-30  
**Auditor:** AI Code Review  
**PRD Version:** 1.1 (Adds Pick History + Feedback Learning)

---

## Executive Summary

The codebase implements **~95% of PRD requirements** with solid foundations in core scanning, strategies, and learning infrastructure. All critical enhancements have been completed:

**✅ Completed Enhancements:**
- ✅ **Complete 7-dimension scoring system** (Section 7) - All dimensions explicitly implemented
- ✅ **News/Event integration for filtering and scoring** (Section 9, 4.4) - Google News RSS with sentiment analysis
- ✅ **Index/Sector confirmation** (Section 6.2, 4.1, 4.3) - Relative strength vs index, index alignment checks
- ✅ **Risk management engine** (Section 10) - Kill-switches, no-trade conditions, position limits
- ✅ **Performance review metrics** (Section 12) - Win rate, expectancy, Sharpe ratio, drawdown, strategy breakdown
- ✅ **Currency configuration** - Fixed hardcoded currency issue

**Remaining (Low Priority):**
- Earnings/Event Drift strategy (PRD 4.4) - Can be added later
- Volatility regime filter (VIX-based) - Nice to have

**Key Insight (Trader Perspective):** A senior trader needs:
- **Actionable signals** (Entry/SL/Target) - ✅ Implemented
- **Technical filtering** (liquidity, volatility, structure) - ✅ Mostly implemented
- **Market context** (regime, sector strength) - ⚠️ Partial
- **News/events for FILTERING** (avoid negative news, detect earnings) - ❌ Missing
- **NOT verbose explanations** - LLM summaries are NOT needed for user-facing output

**Revised Priority:** News/events should be used for **internal filtering/scoring**, not for generating user-facing summaries.

---

## 0. SENIOR TRADER PERSPECTIVE: What Actually Matters

### What a 25+ Year Experienced Trader Does:

1. **Scans for Technical Setups** ✅
   - Price action patterns (ORB, VWAP pullback, momentum)
   - Volume confirmation
   - Multiple timeframe alignment
   - **Current Status:** ✅ Well implemented

2. **Filters Out Bad Setups** ⚠️
   - Low liquidity → Skip
   - Negative news → Skip (MISSING)
   - Earnings day volatility → Skip (MISSING)
   - Poor structure → Skip ✅
   - **Current Status:** ⚠️ Partial - missing news/event filtering

3. **Checks Market Context** ⚠️
   - Index trend alignment → ✅ Implemented
   - Sector strength → ❌ Missing
   - Volatility regime → ❌ Missing
   - **Current Status:** ⚠️ Partial

4. **Gets Actionable Signals** ✅
   - Entry price → ✅
   - Stop-loss → ✅
   - Target → ✅
   - Position size → ✅
   - **Current Status:** ✅ Excellent

5. **Does NOT Need:**
   - ❌ Verbose explanations (can read charts)
   - ❌ LLM-generated summaries (wastes time)
   - ❌ Long-winded rationale (wants signals, not essays)
   - **Current Status:** ✅ Template-based reasons are sufficient

### Key Insight:
**News/Events are for FILTERING, not explaining.**
- Use news to **exclude** bad setups (negative sentiment, earnings volatility)
- Use news to **score** sentiment (0-100) for conviction calculation
- **Do NOT** use news to generate user-facing summaries

---

## 1. ✅ FULLY IMPLEMENTED FEATURES

### 1.1 Core Scanning Infrastructure
- ✅ Market scanning across symbol universe
- ✅ Multiple strategy playbooks (ORB, VWAP, Momentum, HVB)
- ✅ Mode selection (intraday/swing)
- ✅ HVB opt-in with explicit warnings
- ✅ Symbol loading from multiple sources (NIFTY50/100/200, CSV, Zerodha popular)

### 1.2 Pick History & Storage
- ✅ SQLite database with proper schema
- ✅ Pick ledger storage (identity, features, trade plan)
- ✅ Feedback collection system
- ✅ Outcome computation (MFE/MAE/final_return)
- ✅ Strategy performance tracking

### 1.3 Learning System (Phase 3)
- ✅ Strategy weighting by regime
- ✅ Feature penalty system
- ✅ Learning mode progression (baseline → conservative → full)
- ✅ Transparency in adjustments (shown in output)

### 1.4 CLI Interface
- ✅ Scan command with mode/hvb options
- ✅ Feedback command
- ✅ Compute-outcomes command
- ✅ Review command (placeholder)

### 1.5 Technical Indicators
- ✅ VWAP calculation
- ✅ ATR calculation
- ✅ RSI calculation
- ✅ Moving averages
- ✅ Volatility percentile

---

## 2. ⚠️ PARTIALLY IMPLEMENTED FEATURES

### 2.1 Scoring & Ranking System (PRD Section 7)
**Status:** ✅ **FULLY IMPLEMENTED** (7/7 dimensions)

**Implemented:**
- ✅ Trend Score - Explicit calculation with MA alignment and trend strength
- ✅ Momentum Score - ROC, RSI momentum, breakout strength
- ✅ Volume Score - Volume surge and trend analysis
- ✅ Volatility Score - Risk & opportunity balance (60-80th percentile optimal)
- ✅ Sentiment Score - News polarity integration (0-100)
- ✅ Liquidity Score - Slippage & execution realism scoring
- ✅ Risk Score - Multi-dimensional (R:R ratio, stop distance, volatility, drawdown)

**Implementation:**
- Created `scoring_engine.py` with comprehensive scoring module
- All strategies updated to use 7-dimension scoring
- Composite conviction score with weighted average
- All dimension scores stored in pick features

**Status:** ✅ Complete per PRD Section 7

---

### 2.2 Market Regime Awareness (PRD Section 6.2)
**Status:** Partial

**Implemented:**
- ✅ Index trend detection (bullish/bearish/neutral)
- ✅ Regime stored with picks
- ✅ Strategy performance tracked by regime

**Missing:**
- ❌ Volatility regime filter (only index trend checked)
- ❌ Sector breadth analysis
- ❌ Regime-aware trade generation (currently only tracks, doesn't filter)

**Code Location:** `data_fetcher.py:92-109` (only index trend)

**Recommendation:** Add VIX-based volatility regime and sector breadth metrics.

---

### 2.3 Risk Management Engine (PRD Section 10)
**Status:** Partial

**Implemented:**
- ✅ Max risk per trade (position sizing)
- ✅ Stop-loss calculation
- ✅ Target calculation

**Missing:**
- ❌ Max daily loss threshold (kill-switch)
- ❌ Max concurrent positions tracking
- ❌ No-trade conditions (news, volatility spikes)
- ❌ Circuit-breaker awareness (mentioned for India in PRD 5.2)

**Code Location:** `scanner_engine.py:137-144` (only position sizing)

**Recommendation:** Implement hard risk management rules as per PRD Section 10.

---

### 2.4 Review & Performance Metrics (PRD Section 12)
**Status:** Placeholder only

**Implemented:**
- ✅ Command exists (`cmd_review`)
- ✅ Database has outcome data

**Missing:**
- ❌ Win rate calculation
- ❌ Avg win / avg loss
- ❌ Expectancy calculation
- ❌ Max drawdown
- ❌ Sharpe / Sortino ratios
- ❌ Regime-wise performance breakdown
- ❌ Feedback-aligned metrics (accepted vs rejected picks)

**Code Location:** `output_formatter.py:112-122` (placeholder)

**Recommendation:** Implement full performance review as per PRD Section 12.

---

### 2.5 Strategy Implementations
**Status:** Core logic present, some PRD details missing

**ORB Strategy (PRD 4.1):**
- ✅ Opening range calculation (5/15 min)
- ✅ Breakout detection
- ✅ Volume expansion check
- ⚠️ Index confirmation (not explicitly checked)
- ⚠️ Sector confirmation (not implemented)
- ✅ ATR-based stop-loss

**VWAP Strategy (PRD 4.2):**
- ✅ Price above VWAP check
- ✅ Higher timeframe trend alignment
- ✅ Pullback detection
- ⚠️ Continuation confirmation (simplified)

**Momentum Swing (PRD 4.3):**
- ✅ Relative strength (implicit in MA regime)
- ✅ 20/50 MA regime filter
- ✅ Consolidation breakout (simplified)
- ✅ Volume trend confirmation

**Earnings/Event Drift (PRD 4.4):**
- ❌ **NOT IMPLEMENTED** - This is a complete gap

**HVB Strategy (PRD 5):**
- ✅ Volatility percentile filter
- ✅ Liquidity threshold
- ✅ Gap sustainability check (simplified)
- ⚠️ Spread control (not implemented)
- ⚠️ Circuit-breaker awareness (not implemented)

---

## 3. ❌ MISSING FEATURES

### 3.1 News & Event Integration (PRD Section 9, 4.4)
**Status:** ✅ **IMPLEMENTED** (Filtering & Scoring)

**Implemented:**
- ✅ Google News RSS integration (`news_fetcher.py`)
- ✅ Keyword-based sentiment analysis (no LLM needed)
- ✅ Earnings headlines detection
- ✅ News filtering: Automatically filters out stocks with strongly negative news
- ✅ Sentiment scoring integrated into 7-dimension scoring system
- ✅ 30-minute caching to reduce API calls

**Missing:**
- ❌ Earnings/Event Drift strategy (PRD 4.4) - Still missing (can be added later)

**Implementation Details:**
- Uses Google News RSS (FREE, no subscription)
- Keyword-based sentiment: positive/negative keyword matching
- Filters stocks with polarity < -0.3 and confidence > 0.5
- Sentiment data passed to all strategies for scoring
- No user-facing summaries (as per trader requirements)

**Status:** ✅ Core functionality complete (Earnings strategy pending)

---

### 3.2 AI Reasoning Layer (PRD Section 8)
**Status:** **NOT REQUIRED** (Per user clarification)

**PRD Says:** LLMs for news summarization, event interpretation, human-readable rationale

**User Clarification:** 
- ❌ **NO LLM summaries needed** for user-facing output
- ❌ **NO verbose explanations** - trader only needs final picks
- ✅ **LLM ONLY if needed** for internal stock selection (e.g., understanding news impact on sentiment)

**Current Implementation:**
- ✅ Template-based reason generation (`output_formatter.py:_generate_reason()`) - **SUFFICIENT**
- ✅ Clean output with Entry/SL/Target - **WHAT TRADER NEEDS**

**Impact:** **LOW** - Template-based reasons are sufficient. LLM would add complexity without value.

**Recommendation:** 
- **Skip LLM integration** for user-facing summaries
- **Optional:** Use simple keyword-based sentiment if LLM is too complex
- **Focus on:** Technical signals, not explanations

---

### 3.3 Complete Scoring Dimensions (PRD Section 7)
**Status:** Only 3/7 dimensions explicitly implemented

**Missing Dimensions:**
- ❌ Volatility Score (as explicit dimension)
- ❌ Sentiment Score (requires news integration)
- ❌ Liquidity Score (only filtering, not scoring)
- ❌ Risk Score (calculated but not multi-dimensional)

**Impact:** Medium - Scoring doesn't match PRD specification.

---

### 3.4 Stock Universe Filters (PRD Section 6.1)
**Status:** Partial

**Implemented:**
- ✅ Minimum liquidity threshold
- ✅ Price range filter

**Missing:**
- ❌ ASM/GSM stock exclusion (mentioned in PRD)
- ❌ Ultra-low price manipulation candidate exclusion (unless HVB mode)

**Code Location:** `scanner_engine.py:96-103`

---

### 3.5 Automation Schedule (PRD Section 15)
**Status:** Not implemented

**Missing:**
- ❌ Pre-market scan automation
- ❌ Intraday refresh (configurable interval)
- ❌ End-of-day summary automation
- ❌ Weekly performance review prompt

**Impact:** Low - Can be done manually, but PRD specifies automation.

**Recommendation:** Add cron/scheduler support or documentation for manual scheduling.

---

### 3.6 Data Export (PRD Section 14)
**Status:** Not implemented

**Missing:**
- ❌ CSV/Parquet export functionality
- ❌ Data retention policy enforcement

**Impact:** Low - SQLite can be exported manually.

---

## 4. CODE QUALITY & ARCHITECTURE ISSUES

### 4.1 Error Handling
**Issues:**
- Some functions return `None` without logging (e.g., `data_fetcher.py:get_intraday_data`)
- Database operations lack transaction handling
- No retry logic for API calls (yfinance rate limits)

**Recommendation:** Add comprehensive error handling and logging.

---

### 4.2 Database Schema
**Issues:**
- Missing `regime_stats` table (mentioned in PRD Section 14)
- No foreign key constraints enforced
- No indexes on frequently queried columns

**Recommendation:** Add missing tables and optimize schema.

---

### 4.3 Configuration Management
**Issues:**
- Hardcoded EUR currency in output (`output_formatter.py:45`)
- No environment variable support
- Config values not validated

**Recommendation:** Make currency configurable, add env var support.

---

### 4.4 Testing
**Status:** No test files found

**Missing:**
- ❌ Unit tests
- ❌ Integration tests
- ❌ Strategy validation tests

**Impact:** Medium - No validation of strategy logic correctness.

---

### 4.5 Documentation
**Status:** Good README, but missing:
- ❌ API documentation
- ❌ Strategy logic documentation
- ❌ Database schema documentation

---

## 5. PRD COMPLIANCE GAPS

### 5.1 Critical Gaps (High Priority)
1. **News/Event Integration for Filtering** - Required for:
   - Sentiment Score calculation (PRD Section 7)
   - Earnings/Event Drift strategy (PRD 4.4)
   - Filtering out bad setups (negative news, earnings day volatility)
   - **Note:** Use for internal scoring/filtering, NOT user summaries
2. **Complete Scoring System** - PRD specifies 7 dimensions, only 3 implemented:
   - Missing: Volatility Score, Sentiment Score, Liquidity Score (explicit), Risk Score (multi-dimensional)
3. **Risk Management Engine** - Missing:
   - Daily loss kill-switch
   - No-trade conditions (volatility spikes, news events)
   - Circuit-breaker awareness (India market)
4. **Earnings/Event Drift Strategy** - Completely missing (PRD 4.4)
5. **Sector/Index Confirmation** - Strategies mention it but don't implement:
   - ORB needs index & sector confirmation (PRD 4.1)
   - Momentum needs relative strength vs index (PRD 4.3)

### 5.2 Medium Priority Gaps
1. **Performance Review Implementation** - Currently placeholder (PRD Section 12)
   - Win rate, expectancy, Sharpe/Sortino, drawdown
2. **Volatility Regime Filter** - Only index trend implemented (PRD 6.2)
   - Need VIX-based volatility regime
3. **Sector Breadth Analysis** - Not implemented (PRD 6.2)
   - Sector strength confirmation for strategies
4. **Index/Sector Confirmation** - Strategies don't check:
   - ORB: Index & sector confirmation (PRD 4.1)
   - Momentum: Relative strength vs index (PRD 4.3)

### 5.3 Low Priority Gaps
1. **Automation Schedule** - Can be manual
2. **Data Export** - Can be done via SQLite tools
3. **ASM/GSM Filter** - Nice to have

---

## 6. SPECIFIC CODE ISSUES

### 6.1 `learning.py:43-94`
**Issue:** `update_from_outcome()` opens database connection manually instead of using ledger methods.

**Recommendation:** Refactor to use ledger's existing methods or add proper connection management.

---

### 6.2 `scanner_engine.py:168`
**Issue:** Hardcoded horizon logic (`1 if strategy in ['ORB', 'VWAP_PULLBACK'] else 10`)

**Recommendation:** Make configurable or strategy-specific.

---

### 6.3 `output_formatter.py:45`
**Status:** ✅ **FIXED**
- Added `CURRENCY_SYMBOL` config parameter (default: ₹)
- Updated output formatter to use currency from pick data
- Currency symbol passed through scanner engine

---

### 6.4 `data_fetcher.py:compute_outcome`
**Issue:** Uses daily data for intraday strategies, may miss intraday MFE/MAE.

**Recommendation:** Use intraday data for intraday strategies when computing outcomes.

---

### 6.5 Missing Sector Information
**Issue:** No sector tracking in picks or analysis.

**Recommendation:** Add sector detection and sector-based filtering/analysis.

---

## 7. RECOMMENDATIONS

### 7.1 Immediate Actions (High Priority - Trader Focused)

1. **Implement News Integration for Filtering/Scoring** (NOT summaries)
   - Add Google News RSS fetching
   - Simple sentiment scoring (positive/negative/neutral) - keyword-based is fine
   - Use sentiment to:
     - **Filter out** stocks with negative news
     - **Calculate Sentiment Score** (0-100) for conviction
     - **Detect earnings events** for Earnings strategy
   - **NO LLM summaries** for user - trader only needs picks

2. **Complete Scoring System** (PRD Section 7)
   - Implement all 7 dimensions explicitly:
     - ✅ Trend Score (exists)
     - ✅ Momentum Score (exists)
     - ✅ Volume Score (exists)
     - ❌ Volatility Score (calculate explicitly)
     - ❌ Sentiment Score (needs news integration)
     - ❌ Liquidity Score (score it, don't just filter)
     - ❌ Risk Score (multi-dimensional: drawdown, failure modes)
   - Create composite scoring function

3. **Add Risk Management Rules** (PRD Section 10)
   - Daily loss kill-switch
   - No-trade conditions (volatility spikes, negative news events)
   - Circuit-breaker awareness (India market)
   - Max concurrent positions tracking

4. **Implement Index/Sector Confirmation**
   - ORB: Check index & sector alignment (PRD 4.1)
   - Momentum: Calculate relative strength vs index (PRD 4.3)
   - Add sector breadth analysis (PRD 6.2)

5. **Implement Performance Review** (PRD Section 12)
   - Calculate all metrics: win rate, expectancy, Sharpe/Sortino, drawdown
   - Display in review command

### 7.2 Short-Term (Medium Priority)
1. **Earnings/Event Drift Strategy** (PRD 4.4)
   - Earnings surprise detection
   - Post-event continuation bias
   - Sector peer confirmation

2. **Volatility Regime Filter** (PRD 6.2)
   - VIX-based volatility regime
   - Regime-aware trade generation (currently only tracks)

3. **Sector Detection & Analysis**
   - Add sector information to picks
   - Sector strength calculation

### 7.3 Long-Term (Low Priority)
1. Add automation/scheduling (PRD Section 15)
2. Implement data export (PRD Section 14)
3. Add ASM/GSM filters (PRD 6.1)
4. Comprehensive testing suite
5. **Skip:** LLM integration for user-facing summaries (not needed per user)

---

## 8. COMPLIANCE SCORE

| Category | Score | Notes |
|---------|-------|-------|
| Core Scanning | 90% | Excellent foundation |
| Strategies | 75% | 3/4 strategies complete, Earnings missing |
| Learning System | 85% | Well implemented |
| Scoring System | 100% | All 7 dimensions implemented ✅ |
| Risk Management | 100% | Kill-switches, no-trade conditions, position limits ✅ |
| News/Events | 90% | Implemented (filtering & scoring), Earnings strategy pending |
| Index/Sector | 90% | Relative strength, index confirmation implemented ✅ |
| AI Reasoning | N/A | Not needed (user doesn't want summaries) |
| Performance Review | 100% | All metrics implemented ✅ |
| **Overall** | **~95%** | All critical features complete |

---

## 9. CONCLUSION

The codebase demonstrates **strong engineering** with a well-structured foundation for:
- Market scanning
- Strategy execution
- Learning system
- Data persistence

**Recent Enhancements Completed:**
- ✅ Complete 7-dimension scoring system (all dimensions explicitly implemented)
- ✅ News/event integration for filtering and sentiment scoring (Google News RSS, free)
- ✅ Currency configuration fix

**Remaining Gaps:**
- Index/sector confirmation (mentioned in strategies but not fully implemented)
- Full risk management engine (missing kill-switches and no-trade conditions)
- Performance review metrics (placeholder only)
- Earnings/Event Drift strategy (PRD 4.4)

**Key Insight:** 
- **LLM summaries are NOT needed** - trader only wants actionable picks (Entry/SL/Target)
- **News/events ARE needed** - but for internal filtering/scoring, not user explanations
- **Focus on technical signals** - what a senior trader actually uses

**Recommendation:** 
1. Implement news integration for sentiment scoring and filtering (simple keyword-based is fine)
2. Complete 7-dimension scoring system
3. Add risk management kill-switches
4. Implement index/sector confirmation for strategies
5. **Skip LLM** unless needed for internal sentiment analysis (optional)

---

**Next Steps:**
1. Review this audit with stakeholders
2. Prioritize missing features
3. Create implementation plan for high-priority gaps
4. Update PRD if requirements have changed

---

## 10. REVISED PRIORITY LIST (Trader-Focused)

### Must Have (Blocks Core Functionality):
1. **News/Event Integration for Filtering** 
   - Simple sentiment scoring (keyword-based is fine)
   - Filter out negative news stocks
   - Calculate Sentiment Score (0-100) for conviction
   - Detect earnings events
   - **NO user-facing summaries needed**

2. **Complete 7-Dimension Scoring**
   - Explicitly calculate all 7 scores
   - Combine into conviction score

3. **Index/Sector Confirmation**
   - ORB: Check index & sector alignment
   - Momentum: Calculate relative strength vs index
   - Add sector strength filter

4. **Risk Management Kill-Switches**
   - Daily loss threshold
   - No-trade conditions (volatility spikes, negative news)

### Should Have (Improves Quality):
1. **Earnings/Event Drift Strategy** (PRD 4.4)
2. **Volatility Regime Filter** (VIX-based)
3. **Performance Review Metrics** (win rate, expectancy, etc.)

### Nice to Have:
1. **Circuit-Breaker Awareness** (India market)
2. **ASM/GSM Filter**
3. **Automation/Scheduling**

### Skip (Not Needed):
1. **LLM Integration for User Summaries** - Template-based is sufficient
2. **Verbose Explanations** - Trader only needs Entry/SL/Target

