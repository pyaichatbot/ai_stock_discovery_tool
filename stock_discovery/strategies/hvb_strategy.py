"""
AI-Powered Stock Discovery Tool - High Volatility Breakout Strategy
⚠️ HIGH RISK MODE - Opt-in only
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np

from ..config import Config
from ..technical_indicators import TechnicalIndicators
from ..scoring_engine import ScoringEngine


class HighVolatilityBreakout:
    """High Volatility Breakout (HVB) Strategy - HIGH RISK"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, symbol: str, daily_df: pd.DataFrame, intraday_df: Optional[pd.DataFrame] = None,
                sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """Detect high-volatility breakout setup"""
        if daily_df is None or daily_df.empty or len(daily_df) < 60:
            return None
        
        try:
            current_price = daily_df['close'].iloc[-1]
            
            # Calculate volatility percentile
            vol_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df, lookback=60)
            
            # Only proceed if volatility is in top 10%
            if vol_percentile < self.config.HVB_MIN_VOLATILITY_PERCENTILE:
                return None
            
            # Check for breakout pattern
            high_20d = daily_df['high'].iloc[-20:].max()
            current_high = daily_df['high'].iloc[-1]
            
            # Must be breaking out to new highs
            breaking_out = current_high >= high_20d * 0.98
            
            if not breaking_out:
                return None
            
            # Volume confirmation
            avg_volume = daily_df['volume'].mean()
            recent_volume = daily_df['volume'].iloc[-3:].mean()
            volume_surge = recent_volume > avg_volume * 1.5
            
            if not volume_surge:
                return None
            
            # Liquidity check (must meet minimum)
            if avg_volume < self.config.MIN_AVG_VOLUME:
                return None
            
            # Calculate stops and targets (wider for HVB)
            atr = TechnicalIndicators.calculate_atr(daily_df)
            if atr == 0:
                atr = current_price * 0.03
            
            stop_loss = current_price - (atr * 2.5)  # Wider stop
            target = current_price + (atr * 5.0)  # Aggressive target
            
            # Calculate potential move
            potential_move_pct = ((target - current_price) / current_price) * 100
            
            # Breakout percentage
            breakout_pct = ((current_high - high_20d) / high_20d) * 100 if high_20d > 0 else 0
            
            # Use comprehensive 7-dimension scoring
            # Note: HVB will have high volatility score and high risk score
            scores = ScoringEngine.calculate_composite_scores(
                daily_df=daily_df,
                intraday_df=intraday_df,
                entry_price=current_price,
                stop_loss=stop_loss,
                target_price=target,
                current_volume=recent_volume,
                volume_surge=volume_surge,
                breakout_pct=breakout_pct,
                volatility_percentile=vol_percentile,
                sentiment_data=sentiment_data,
                min_avg_volume=self.config.MIN_AVG_VOLUME
            )
            
            # Override risk score for HVB (always high risk)
            scores['risk_score'] = max(85.0, scores['risk_score'])
            
            return {
                'strategy': 'HVB',
                'entry_price': float(current_price),
                'stop_loss': float(stop_loss),
                'target_price': float(target),
                'conviction_score': scores['conviction_score'],
                'risk_score': scores['risk_score'],
                'risk_label': '⚠️ HIGH RISK',
                'features': {
                    'volatility_percentile': float(vol_percentile),
                    'potential_move_pct': float(potential_move_pct),
                    'volume_surge': volume_surge,
                    'avg_volume': float(avg_volume),
                    'atr': float(atr),
                    'breakout_pct': float(breakout_pct),
                    'warning': 'High volatility - expect large swings both ways'
                },
                'dimension_scores': scores['dimension_scores']
            }
        
        except Exception as e:
            print(f"HVB analysis error for {symbol}: {e}")
            return None
