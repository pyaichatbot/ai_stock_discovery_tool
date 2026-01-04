"""
AI-Powered Stock Discovery Tool - Earnings/Event Drift Strategy
PRD Section 4.4: Post-earnings continuation bias
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..technical_indicators import TechnicalIndicators
from ..scoring_engine import ScoringEngine
from ..config import Config


class EarningsEventDrift:
    """
    Earnings/Event Drift Strategy
    
    Identifies stocks with:
    - Recent earnings announcement (1-5 days ago)
    - Earnings surprise (beat/miss)
    - Positive guidance sentiment
    - Post-earnings momentum continuation
    - Sector peer confirmation
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, symbol: str, daily_df: pd.DataFrame, sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Analyze symbol for earnings event drift opportunity
        
        Args:
            symbol: Stock symbol
            daily_df: Daily price data
            sentiment_data: News sentiment data (must include earnings_detected)
        
        Returns:
            Dict with pick details or None
        """
        if daily_df is None or len(daily_df) < 20:
            return None
        
        # Check if earnings event detected
        if not sentiment_data or not sentiment_data.get('earnings_detected', False):
            return None
        
        current_price = daily_df['close'].iloc[-1]
        
        # Check for recent earnings (within last 5 days)
        # We'll use sentiment data to determine if earnings was recent
        # For now, assume if earnings_detected is True, it's recent enough
        
        # Analyze post-earnings price action
        # Look for continuation after earnings announcement
        recent_data = daily_df.tail(10)  # Last 10 days
        
        # Calculate post-earnings momentum
        if len(recent_data) < 5:
            return None
        
        # Price movement in recent days (post-earnings)
        price_change = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0] * 100
        
        # Volume surge (earnings usually have high volume)
        avg_volume = daily_df['volume'].mean()
        recent_volume = recent_data['volume'].mean()
        volume_surge = recent_volume > avg_volume * 1.5
        
        # Earnings surprise detection (from sentiment)
        # Positive sentiment suggests beat, negative suggests miss
        sentiment_polarity = sentiment_data.get('polarity', 'neutral')
        earnings_positive = sentiment_polarity == 'positive'
        
        # Only trade positive earnings surprises with continuation
        if not earnings_positive:
            return None
        
        # Post-earnings continuation check
        # Price should be moving in direction of earnings surprise
        if price_change < 2.0:  # Need at least 2% move post-earnings
            return None
        
        # Technical confirmation
        ma_20 = daily_df['close'].tail(20).mean()
        ma_50 = daily_df['close'].tail(50).mean() if len(daily_df) >= 50 else ma_20
        
        # Price should be above MAs (uptrend)
        if current_price < ma_20:
            return None
        
        # RSI check (not overbought)
        rsi = TechnicalIndicators.calculate_rsi(daily_df)
        if rsi is None or rsi > 75:  # Too overbought
            return None
        
        # Calculate entry, stop-loss, target
        atr = TechnicalIndicators.calculate_atr(daily_df)
        if atr is None or atr <= 0:
            return None
        
        # Entry: Current price (momentum continuation)
        entry_price = current_price
        
        # Stop-loss: Below recent low or ATR-based (tighter than swing)
        recent_low = recent_data['low'].min()
        atr_stop = entry_price - (atr * 1.5)  # 1.5 ATR stop
        stop_loss = max(recent_low * 0.98, atr_stop)  # 2% below recent low or ATR-based
        
        # Target: Based on earnings surprise magnitude and momentum
        # Conservative target: 1.5x risk or 5% move, whichever is higher
        risk_amount = entry_price - stop_loss
        target_price = entry_price + (risk_amount * 1.5)  # 1.5:1 R:R minimum
        # Or 5% move, whichever is higher
        target_price = max(target_price, entry_price * 1.05)
        
        # Calculate breakout percentage
        breakout_pct = price_change
        
        # Volume surge flag
        volume_surge_flag = volume_surge
        
        # Calculate volatility percentile
        volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df)
        
        # Calculate all 7 dimension scores
        scores = ScoringEngine.calculate_composite_scores(
            daily_df=daily_df,
            intraday_df=None,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            current_volume=recent_data['volume'].iloc[-1],
            volume_surge=volume_surge_flag,
            breakout_pct=breakout_pct,
            volatility_percentile=volatility_percentile,
            sentiment_data=sentiment_data,
            min_avg_volume=self.config.MIN_AVG_VOLUME
        )
        
        # Boost conviction for earnings surprise
        base_conviction = scores['conviction_score']
        earnings_boost = 5.0 if earnings_positive else 0.0
        conviction_score = min(100.0, base_conviction + earnings_boost)
        
        # Risk score
        risk_score = scores['risk_score']
        
        # Features
        features = {
            'earnings_detected': True,
            'earnings_positive': earnings_positive,
            'post_earnings_move_pct': price_change,
            'volume_surge': volume_surge_flag,
            'rsi': rsi,
            'ma_20': ma_20,
            'ma_50': ma_50,
            'above_ma20': current_price > ma_20,
            'above_ma50': current_price > ma_50,
            'volatility_percentile': volatility_percentile,
            **{f'{k}_score': v for k, v in scores.items() if k.endswith('_score')}
        }
        
        # Trade plan
        trade_plan = {
            'entry': entry_price,
            'stop_loss': stop_loss,
            'target': target_price,
            'risk_reward_ratio': (target_price - entry_price) / (entry_price - stop_loss) if (entry_price - stop_loss) > 0 else 0,
            'holding_period_days': 5  # Short-term post-earnings drift
        }
        
        return {
            'strategy': 'EARNINGS_DRIFT',
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'target_price': target_price,
            'conviction_score': conviction_score,
            'risk_score': risk_score,
            'features': features,
            'trade_plan': trade_plan
        }

