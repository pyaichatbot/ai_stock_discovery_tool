# AI-Powered Stock Discovery Tool (Mac-Only)
## Project Requirements Document (PRD)

**Version:** 1.1 (Adds Pick History + Feedback Learning)  
**Scope:** Personal Use (Local Execution Only)  
**Platform:** macOS (Apple Silicon / Intel)  
**Mode:** Market Analysis & Stock Identification (No Trading Automation)

---

## 1. Purpose & Vision

Build a **fully automated, AI-assisted stock discovery system** that:
- Scans the entire market (no manual stock input)
- Identifies **intraday** and **short-term** trading opportunities
- Outputs **actionable trade setups** with reasoning
- Matches the **process quality of senior discretionary traders**
- **Learns from your feedback + outcomes over time** (personalized improvement loop)

The system is **decision-support only**. All execution decisions remain manual.

---

## 2. Core Design Principles

1. **Automation over prediction**  
   The system finds opportunities; it does not “promise outcomes”.

2. **Process > accuracy claims**  
   Performance is evaluated using professional metrics:
   - Expectancy
   - Drawdown
   - Risk-adjusted returns

3. **Strategy ensembles, not a single AI brain**  
   Multiple independent playbooks reduce regime risk.

4. **Explicit risk labeling**  
   High-reward modes are clearly marked as **HIGH RISK**.

5. **Continuous learning from outcomes**  
   Picks are stored, evaluated, and improved using:
   - realized outcomes
   - user feedback
   - strategy-level performance tracking
   - regime-aware weighting

---

## 3. Supported Trading Horizons

### 3.1 Intraday Trading
- Timeframe: 1–15 minute candles
- Holding period: minutes to same day
- Objective: momentum & volatility capture

### 3.2 Short-Term Trading (Swing)
- Timeframe: daily candles
- Holding period: 2–30 trading days
- Objective: trend continuation & post-event drift

---

## 4. Strategy Playbooks (Core Logic)

### 4.1 Intraday – Opening Range Breakout (ORB)
**Risk:** Medium

- First 5/15 minute high–low range
- Breakout with volume expansion
- Index & sector confirmation
- ATR-based stop-loss

---

### 4.2 Intraday – VWAP Trend Pullback
**Risk:** Medium

- Price above rising VWAP
- Higher timeframe trend alignment
- Pullback to VWAP / EMA
- Continuation confirmation

---

### 4.3 Short-Term – Momentum Swing
**Risk:** Medium

- Relative strength vs index
- 20/50 MA regime filter
- Consolidation breakout
- Volume trend confirmation

---

### 4.4 Short-Term – Earnings / Event Drift
**Risk:** Medium–High

- Earnings surprise detection
- Guidance sentiment analysis
- Sector peer confirmation
- Post-event continuation bias

---

## 5. High-Volatility Breakout Mode (HVB)

### ⚠️ EXPLICIT HIGH-RISK MODE

This mode is **opt-in only** and clearly labeled.

**Objective:** Identify stocks with potential **10–30%+ short-term moves**  
(High variance; can also produce large losses due to gaps/slippage.)

### 5.1 Characteristics
- Small / mid-cap bias
- Extreme volatility
- News or structural catalysts
- High slippage & gap risk

### 5.2 Filters (Mandatory)
- Liquidity threshold (min avg volume)
- Spread control
- Circuit-breaker awareness (India)
- Gap sustainability check

### 5.3 Use Cases
- Capitalizing on news-driven momentum
- Identifying early-stage breakouts
- NOT suitable for conservative capital

### 5.4 Output Labeling
Every HVB setup must include:
- **HIGH RISK** flag
- Volatility percentile
- Worst-case scenario description
- Strict stop-loss guidance

---

## 6. Market Universe Selection

### 6.1 Stock Filters
- Minimum liquidity thresholds
- Exclude chronic ASM/GSM stocks
- Exclude ultra-low price manipulation candidates (unless HVB mode)

### 6.2 Regime Awareness
- Index trend filter (e.g., NIFTY)
- Volatility regime filter
- Sector breadth analysis

Trades are only generated when the regime supports the strategy.

---

## 7. Scoring & Ranking System

Each candidate stock is scored across multiple dimensions:

| Dimension | Description |
|---------|------------|
| Trend Score | Strength & direction of price trend |
| Momentum Score | Rate of change & breakout strength |
| Volume Score | Participation & confirmation |
| Volatility Score | Risk & opportunity balance |
| Sentiment Score | News & event polarity |
| Liquidity Score | Slippage & execution realism |
| Risk Score | Drawdown & failure modes |

### Composite Outputs
- **Conviction Score:** 0–100
- **Risk Score:** 0–100
- **Strategy Tag**
- **Trade Plan:** Entry / SL / Target (indicative)

---

## 8. AI Reasoning Layer (LLM Usage)

LLMs are used for:
- News summarization
- Event interpretation
- Human-readable trade rationale
- Risk explanation

LLMs are **NOT** used to directly generate buy/sell signals.

---

## 9. Data Sources

### Price & Volume
- Broker-grade intraday feeds (recommended)
- Yahoo Finance (daily fallback)
- Alpha Vantage (backup)

### News & Events
- Google News RSS
- Company announcements
- Earnings headlines

---

## 10. Risk Management Engine

Hard rules enforced by the system:
- Max risk per trade (configurable)
- Max daily loss threshold (kill-switch)
- Max concurrent positions (simulation)
- No-trade conditions (news, volatility spikes)

---

## 11. Pick History, Feedback, and Learning Loop (NEW)

### 11.1 Goal
Store every generated pick, track what happened after, collect your feedback, and use both to improve future picks.

This turns the system into a **personalized trader assistant** that learns your preferences (risk tolerance, style) and which strategies actually work in your market conditions.

---

### 11.2 Data Stored Per Pick (Pick Ledger)
For each pick, store:

**Identity**
- Symbol, exchange, sector
- Strategy tag (ORB/VWAP/Swing/Earnings/HVB)
- Timestamp generated
- Market regime snapshot (index trend, volatility regime)

**Signal Features (at time of pick)**
- Key indicators used (e.g., RSI, MA regime, volume spike %, gap %)
- Liquidity/spread metrics
- News sentiment summary + score
- Conviction score, risk score

**Trade Plan (suggested)**
- Entry zone
- Stop-loss
- Target(s)
- Time horizon (intraday / swing)
- Risk label (normal / HIGH RISK for HVB)

**Outcomes (computed later)**
- Max favorable excursion (MFE) within horizon
- Max adverse excursion (MAE) within horizon
- Best achievable return under the plan (modelled)
- Return at horizon end (e.g., EOD for intraday, day+10 for swing)
- Hit/miss for stop-loss/target conditions (simulated)

**User Feedback (manual)**
- “Took trade?” (yes/no)
- “Execution notes” (slippage, missed entry, emotions)
- “Quality rating” (1–5)
- “Why rejected?” (if not taken: too risky, unclear catalyst, low liquidity, etc.)
- “Lesson learned” free-text note

---

### 11.3 Feedback UX (Local)
Provide a minimal flow after each scan:
- Show today’s picks
- For each pick: quick actions
  - ✅ mark “took”
  - ❌ mark “skipped”
  - ⭐ rating 1–5
  - 📝 note (optional)

Also allow end-of-day/week “review mode”:
- summarize performance
- ask for lessons learned
- tag recurring issues

---

### 11.4 Learning / Adaptation Rules (How Feedback Changes Future Picks)

**A) Strategy Weighting (Bandit-style)**
- Maintain per-strategy performance by regime (e.g., ORB works in trending days; HVB works only in high-volatility days).
- Increase/decrease strategy weights based on rolling expectancy.

**B) Feature Penalties**
If repeated failures correlate with a feature pattern, penalize it. Examples:
- “low liquidity + HVB” → reduce score
- “gap > X without volume confirmation” → reduce score
- “negative sentiment + weak structure” → exclude

**C) Personal Preference Modeling**
Learn what *you* tend to accept and what performs best for *you*:
- penalize setups you consistently reject
- promote setups you rate highly

**D) Guardrails**
- Never allow learning to override hard risk rules.
- HVB mode cannot silently activate; always opt-in.

---

### 11.5 Output Transparency
Every time learning affects a pick, show:
- “Adjusted by feedback: +6 score due to ORB performing well in this regime”
- “Penalty applied: low liquidity flagged from past underperformance”

No hidden changes.

---

## 12. Evaluation & Validation

### Metrics Tracked
- Win rate
- Avg win / avg loss
- Expectancy
- Max drawdown
- Sharpe / Sortino
- Regime-wise performance
- **Feedback-aligned metrics** (accepted picks vs rejected picks performance)

### Validation Approach
- Historical backtesting
- Walk-forward testing
- Paper-trade simulation
- **Ongoing live journaling** (your pick ledger)

---

## 13. User Interface (Local)

### Supported Interfaces
- CLI commands (primary)
- Optional local web dashboard (FastAPI)

### Example Commands
```bash
scan intraday
scan swing
scan hvb --high-risk
review today
review week
feedback add --pick-id <id> --took yes --rating 4 --note "Entry was late but setup valid"
```

---

## 14. Storage & Persistence

### Local Database
- SQLite (recommended) or DuckDB
- Tables:
  - `picks`
  - `features_snapshot`
  - `outcomes`
  - `feedback`
  - `strategy_stats`
  - `regime_stats`

### Data Retention
- Keep at least 12–24 months of picks
- Export to CSV/Parquet for offline analysis

---

## 15. Automation Schedule

- Pre-market scan
- Intraday refresh (configurable interval)
- End-of-day summary & outcome computation
- Weekly performance review prompt

---

## 16. Explicit Non-Goals

- ❌ No auto trading
- ❌ No broker order placement
- ❌ No return guarantees
- ❌ No real-money execution
- ❌ No mobile app

---

## 17. Legal & Safety Disclaimer

This tool is for **personal market research only**.

- No investment advice
- No guarantee of returns
- Markets involve risk
- User retains full responsibility for decisions

---

## 18. Success Criteria (Personal Use)

- Reduced decision fatigue
- Improved trade selection discipline
- Consistent, explainable process
- Performance comparable to discretionary trading benchmarks
- **Improving quality over time** due to pick history + feedback loop

---

## 19. Future (Optional)

- Broker execution assist (manual)
- Strategy optimization
- Multi-market expansion
- UI enhancements
- More advanced learning (offline training with your pick ledger)

---

## Final Statement

This system succeeds by:
- Discipline over prediction
- Risk control over hype
- Process over promises
- Learning from your own real outcomes

That is how professionals improve.
