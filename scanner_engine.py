"""
AI-Powered Stock Discovery Tool - Scanner Engine
"""

from typing import List, Dict, Optional
from datetime import datetime

from config import Config
from database import PickLedger
from data_fetcher import MarketDataFetcher
from learning import LearningEngine
from news_fetcher import NewsFetcher
from market_context import MarketContext
from risk_manager import RiskManager
from technical_indicators import TechnicalIndicators
from fundamental_analyzer import FundamentalAnalyzer

from strategies.orb_strategy import OpeningRangeBreakout
from strategies.vwap_strategy import VWAPPullback
from strategies.momentum_strategy import MomentumSwing
from strategies.hvb_strategy import HighVolatilityBreakout
from strategies.earnings_strategy import EarningsEventDrift
from multi_timeframe import MultiTimeframeAnalyzer


class ScannerEngine:
    """Main scanner orchestrator with learning integration"""
    
    def __init__(self, config: Config):
        self.config = config
        self.fetcher = MarketDataFetcher()
        self.ledger = PickLedger()
        self.learning = LearningEngine(config, self.ledger)
        self.news_fetcher = NewsFetcher(cache_duration_minutes=30)
        self.market_context = MarketContext()
        self.risk_manager = RiskManager(config, self.ledger)
        self.fundamental_analyzer = FundamentalAnalyzer()
        
        # Initialize strategies
        self.orb = OpeningRangeBreakout(config)
        self.vwap = VWAPPullback(config)
        self.momentum = MomentumSwing(config)
        self.hvb = HighVolatilityBreakout(config)
        self.earnings = EarningsEventDrift(config)
        self.mtf_analyzer = MultiTimeframeAnalyzer()
    
    def scan_market(self, mode: str = "intraday", enable_hvb: bool = False, enable_penny_stock: bool = False) -> List[Dict]:
        """
        Scan entire market and return top picks
        
        Args:
            mode: 'intraday' or 'swing'
            enable_hvb: Enable high-risk HVB mode (opt-in)
            enable_penny_stock: Enable penny stock mode (opt-in, high risk)
        """
        print(f"🔍 Scanning {len(self.config.NIFTY_SYMBOLS)} stocks...")
        
        # Penny stock mode warning
        if enable_penny_stock:
            print("⚠️  PENNY STOCK MODE ENABLED - HIGH RISK")
            print("   • Stocks priced ₹1-50 only")
            print("   • Higher volatility and manipulation risk")
            print("   • Stricter position limits applied")
            print("   • Use with extreme caution!")
            print("")
        
        # Check market regime
        index_trend = self.fetcher.get_index_trend()
        print(f"📊 NIFTY Trend: {index_trend.upper()}")
        
        # Check risk management (kill-switches)
        risk_check = self.risk_manager.can_trade("MARKET_SCAN")
        if not risk_check['allowed']:
            print(f"⚠️  RISK MANAGEMENT: {risk_check['reason']}")
            print("   Trading halted by risk management system")
            return []
        else:
            print(f"✅ Risk checks passed: {risk_check['reason']}")
        
        # Show learning status
        learning_mode = self.learning.get_learning_mode()
        print(f"🧠 Learning Mode: {learning_mode.upper()}")
        
        if learning_mode != "baseline":
            weights = self.learning.get_strategy_weights()
            print(f"📈 Strategy Weights: {weights}")
        
        candidates = []
        hvb_count = 0
        
        for symbol in self.config.NIFTY_SYMBOLS:
            pick = self._analyze_symbol(symbol, mode, index_trend, enable_hvb, enable_penny_stock)
            
            if pick:
                # Apply learning adjustments
                if self.learning.should_learn():
                    pick = self.learning.apply_learning_to_score(pick, index_trend)
                
                # Check if still meets minimum conviction after adjustments
                if pick['conviction_score'] >= self.config.MIN_CONVICTION_SCORE:
                    # Limit HVB picks
                    if pick['strategy'] == 'HVB':
                        if hvb_count < self.config.HVB_MAX_PICKS:
                            candidates.append(pick)
                            hvb_count += 1
                    else:
                        candidates.append(pick)
        
        # Sort by conviction and take top N
        candidates.sort(key=lambda x: x['conviction_score'], reverse=True)
        
        # Apply penny stock limit if enabled
        if enable_penny_stock:
            penny_picks = [p for p in candidates if p.get('is_penny_stock', False)]
            normal_picks = [p for p in candidates if not p.get('is_penny_stock', False)]
            # Limit penny stock picks
            penny_picks = penny_picks[:self.config.PENNY_STOCK_MAX_PICKS]
            # Combine: penny stocks first (up to limit), then normal picks
            top_picks = (penny_picks + normal_picks)[:self.config.TOP_N_PICKS]
        else:
            top_picks = candidates[:self.config.TOP_N_PICKS]
        
        # Save to ledger
        for pick in top_picks:
            pick['market_regime'] = index_trend
            self.ledger.save_pick(pick)
        
        return top_picks
    
    def _analyze_symbol(self, symbol: str, mode: str, regime: str, enable_hvb: bool, enable_penny_stock: bool = False) -> Optional[Dict]:
        """Run all strategies on a symbol"""
        # Fetch data
        daily_df = self.fetcher.get_stock_data(symbol, period="60d", interval="1d")
        
        if daily_df is None or len(daily_df) < 20:
            return None
        
        # Apply filters
        current_price = daily_df['close'].iloc[-1]
        avg_volume = daily_df['volume'].mean()
        
        # Price filtering (different logic for penny stock mode)
        if enable_penny_stock:
            # Penny stock mode: only stocks between PENNY_STOCK_MIN_PRICE and PENNY_STOCK_MAX_PRICE
            if (current_price < self.config.PENNY_STOCK_MIN_PRICE or 
                current_price > self.config.PENNY_STOCK_MAX_PRICE):
                return None
        else:
            # Normal mode: exclude penny stocks (MIN_PRICE to MAX_PRICE)
            if (current_price < self.config.MIN_PRICE or 
                current_price > self.config.MAX_PRICE):
                return None
        
        # Volume filter applies to both modes
        if avg_volume < self.config.MIN_AVG_VOLUME:
            return None
        
        # Circuit breaker check: Skip stocks in trading halt
        if self.market_context.is_circuit_breaker_hit(symbol):
            return None  # Filtered out: circuit breaker hit
        
        # Circuit breaker check: Skip stocks in trading halt
        if self.market_context.is_circuit_breaker_hit(symbol):
            return None  # Filtered out: circuit breaker hit
        
        # Risk management: Check if we can trade this symbol
        volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df) if daily_df is not None else None
        risk_check = self.risk_manager.can_trade(symbol, volatility_percentile)
        if not risk_check['allowed']:
            return None  # Filtered out by risk management
        
        # Fundamental research: Check fundamentals before picking
        fundamental_check = self.fundamental_analyzer.analyze(symbol)
        if not fundamental_check['allowed']:
            return None  # Filtered out by fundamental analysis
        
        # News filtering: Check for negative news and filter out if too negative
        try:
            if self.news_fetcher.should_filter_out(symbol, negative_threshold=-0.3):
                return None  # Filter out stocks with strongly negative news
        except Exception as e:
            # If news fetch fails, continue (don't block scanning)
            pass
        
        # Get sentiment data for scoring (including earnings detection)
        sentiment_data = None
        try:
            sentiment = self.news_fetcher.get_sentiment_for_symbol(symbol)
            sentiment_data = {
                'polarity': sentiment['polarity'],
                'confidence': sentiment['confidence'],
                'earnings_detected': sentiment.get('earnings_detected', False)
            }
        except Exception as e:
            # If sentiment fetch fails, continue without sentiment (neutral)
            pass
        
        results = []
        
        # Intraday strategies
        if mode == "intraday":
            intraday_df = self.fetcher.get_intraday_data(symbol)
            
            if intraday_df is not None and not intraday_df.empty:
                orb_signal = self.orb.analyze(symbol, intraday_df, daily_df, sentiment_data)
                if orb_signal:
                    results.append(orb_signal)
                
                vwap_signal = self.vwap.analyze(symbol, intraday_df, daily_df, sentiment_data)
                if vwap_signal:
                    results.append(vwap_signal)
        
        # Swing strategies (always evaluated)
        momentum_signal = self.momentum.analyze(symbol, daily_df, sentiment_data)
        if momentum_signal:
            results.append(momentum_signal)
        
        # Earnings/Event Drift strategy (only if earnings detected)
        if sentiment_data and sentiment_data.get('earnings_detected', False):
            earnings_signal = self.earnings.analyze(symbol, daily_df, sentiment_data)
            if earnings_signal:
                results.append(earnings_signal)
        
        # HVB (only if explicitly enabled)
        if enable_hvb and self.config.HVB_ENABLED:
            hvb_signal = self.hvb.analyze(symbol, daily_df, None, sentiment_data)
            if hvb_signal:
                results.append(hvb_signal)
        
        if not results:
            return None
        
        # Take best strategy for this symbol
        best = max(results, key=lambda x: x['conviction_score'])
        
        # Circuit breaker warning: Check if near circuit breaker
        near_circuit_breaker = self.market_context.is_near_circuit_breaker(symbol)
        if near_circuit_breaker:
            if 'features' not in best:
                best['features'] = {}
            best['features']['near_circuit_breaker'] = True
            best['risk_warning'] = 'Near circuit breaker - high volatility risk'
        
        # Index/Sector confirmation (PRD 4.1, 4.3)
        index_confirmation = self.market_context.check_index_confirmation(symbol, regime)
        
        # For ORB and Momentum, require index confirmation
        if best['strategy'] in ['ORB', 'MOMENTUM_SWING']:
            if not index_confirmation['confirmed']:
                return None  # Filter out if not confirmed by index
        
        # Add market context to features
        if 'features' not in best:
            best['features'] = {}
        best['features']['index_confirmation'] = index_confirmation['confirmed']
        best['features']['relative_strength'] = index_confirmation.get('relative_strength')
        best['features']['index_trend'] = index_confirmation.get('index_trend')
        
        # Calculate position size (stricter for penny stocks)
        if enable_penny_stock:
            risk_amount = self.config.TOTAL_BUDGET * self.config.PENNY_STOCK_MAX_RISK_PCT
        else:
            risk_amount = self.config.TOTAL_BUDGET * self.config.MAX_RISK_PER_TRADE
        
        risk_per_share = abs(best['entry_price'] - best['stop_loss'])
        
        if risk_per_share > 0:
            position_size = risk_amount / risk_per_share
        else:
            position_size = 0
        
        # Mark as penny stock in features
        if enable_penny_stock:
            if 'features' not in best:
                best['features'] = {}
            best['features']['penny_stock'] = True
            best['is_penny_stock'] = True
        
        # Add multi-timeframe analysis
        try:
            mtf_analysis = self.mtf_analyzer.analyze(symbol)
            best['multi_timeframe'] = mtf_analysis
            
            # Filter out if higher timeframes are bearish (optional - can be configurable)
            # For now, just add it to features for display
            if mtf_analysis['alignment'] == 'bearish' and mtf_analysis['alignment_strength'] >= 0.8:
                # Strong bearish alignment - lower conviction
                best['conviction_score'] = best['conviction_score'] * 0.8
                if 'features' not in best:
                    best['features'] = {}
                best['features']['bearish_higher_timeframe'] = True
        except Exception as e:
            # If MTF analysis fails, continue without it
            pass
        
        # Generate pick ID
        pick_id = f"{symbol.replace('.NS', '')}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # Add fundamental data to pick
        fundamental_check = self.fundamental_analyzer.analyze(symbol)
        if 'features' not in best:
            best['features'] = {}
        best['features']['fundamental_score'] = fundamental_check.get('fundamental_score', 50.0)
        best['features']['fundamental_metrics'] = fundamental_check.get('metrics', {})
        best['fundamental_score'] = fundamental_check.get('fundamental_score', 50.0)
        best['fundamental_metrics'] = fundamental_check.get('metrics', {})
        
        return {
            'pick_id': pick_id,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'position_size': float(position_size),
            'currency_symbol': self.config.CURRENCY_SYMBOL,
            **best
        }
    
    def compute_outcomes_for_pending_picks(self):
        """
        Compute outcomes for picks that don't have outcomes yet
        This should be run daily after market close
        """
        pending = self.ledger.get_picks_without_outcomes()
        
        print(f"📊 Computing outcomes for {len(pending)} pending picks...")
        
        for pick in pending:
            # Determine horizon based on strategy
            horizon_days = 1 if pick['strategy'] in ['ORB', 'VWAP_PULLBACK'] else 10
            
            # Compute outcome
            outcome = self.fetcher.compute_outcome(
                pick['symbol'],
                pick['entry_price'],
                pick['stop_loss'],
                pick['target_price'],
                pick['timestamp'],
                horizon_days
            )
            
            # Save outcome
            self.ledger.save_outcome(
                pick['pick_id'],
                outcome['mfe'],
                outcome['mae'],
                outcome['final_return'],
                outcome['hit_target'],
                outcome['hit_stop']
            )
            
            # Update learning
            self.learning.update_from_outcome(pick['pick_id'], outcome)
            
            print(f"  ✓ {pick['symbol']}: {outcome['final_return']:.2f}% return")
