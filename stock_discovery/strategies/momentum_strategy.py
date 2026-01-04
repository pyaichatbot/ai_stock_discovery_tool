"""
AI-Powered Stock Discovery Tool - Momentum Swing Strategy
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np

from ..config import Config
from ..technical_indicators import TechnicalIndicators
from ..scoring_engine import ScoringEngine


class MomentumSwing:
    """Momentum Swing Trading Strategy"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, symbol: str, daily_df: pd.DataFrame, sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """Detect momentum swing setup"""
        if daily_df is None or daily_df.empty or len(daily_df) < 50:
            return None
        
        try:
            current_price = daily_df['close'].iloc[-1]
            
            # Calculate MAs and RSI
            mas = TechnicalIndicators.calculate_moving_averages(
                daily_df, 
                self.config.MOMENTUM_MA_SHORT, 
                self.config.MOMENTUM_MA_LONG
            )
            rsi = TechnicalIndicators.calculate_rsi(daily_df)
            atr = TechnicalIndicators.calculate_atr(daily_df)
            
            # Check conditions
            ma_bullish = mas['ma_cross']
            rsi_acceptable = 40 < rsi < 70
            
            # Volume trend
            recent_volume = daily_df['volume'].iloc[-5:].mean()
            older_volume = daily_df['volume'].iloc[-20:-5].mean()
            volume_trend = recent_volume > older_volume
            
            if not (ma_bullish and rsi_acceptable):
                return None
            
            # Stops and targets
            if atr == 0:
                atr = current_price * 0.02
            
            stop_loss = mas['ma_short'] - atr
            target = current_price + (atr * 3.0)
            
            # Calculate volatility percentile
            volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df)
            
            # Current volume
            current_volume = recent_volume
            
            # Use comprehensive 7-dimension scoring
            scores = ScoringEngine.calculate_composite_scores(
                daily_df=daily_df,
                intraday_df=None,  # Swing strategy uses daily data
                entry_price=current_price,
                stop_loss=stop_loss,
                target_price=target,
                current_volume=current_volume,
                volume_surge=volume_trend,
                breakout_pct=0.0,  # Not a breakout pattern
                volatility_percentile=volatility_percentile,
                sentiment_data=sentiment_data,
                min_avg_volume=self.config.MIN_AVG_VOLUME
            )
            
            return {
                'strategy': 'MOMENTUM_SWING',
                'entry_price': float(current_price),
                'stop_loss': float(stop_loss),
                'target_price': float(target),
                'conviction_score': scores['conviction_score'],
                'risk_score': scores['risk_score'],
                'features': {
                    'rsi': float(rsi),
                    'ma_short': float(mas['ma_short']),
                    'ma_long': float(mas['ma_long']),
                    'volume_trend_up': volume_trend,
                    'atr': float(atr),
                    'volatility_percentile': float(volatility_percentile)
                },
                'dimension_scores': scores['dimension_scores']
            }
        
        except Exception as e:
            print(f"Momentum analysis error for {symbol}: {e}")
            return None
