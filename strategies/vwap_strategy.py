"""
AI-Powered Stock Discovery Tool - VWAP Pullback Strategy
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np

from config import Config
from technical_indicators import TechnicalIndicators
from scoring_engine import ScoringEngine


class VWAPPullback:
    """VWAP Trend Pullback Strategy"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, symbol: str, intraday_df: pd.DataFrame, daily_df: pd.DataFrame,
                sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """Detect VWAP pullback setup"""
        if intraday_df is None or intraday_df.empty or len(intraday_df) < 50:
            return None
        
        try:
            # Calculate VWAP
            vwap = TechnicalIndicators.calculate_vwap(intraday_df)
            
            if vwap == 0:
                return None
            
            current_price = intraday_df['close'].iloc[-1]
            
            # Check if price near VWAP (within 1%)
            distance_from_vwap = abs(current_price - vwap) / vwap
            near_vwap = distance_from_vwap < 0.01
            above_vwap = current_price > vwap * 0.998
            
            # Check daily trend
            uptrend = True
            if daily_df is not None and not daily_df.empty and len(daily_df) >= 20:
                mas = TechnicalIndicators.calculate_moving_averages(daily_df, 20, 50)
                uptrend = mas['ma_cross']
            
            if not (near_vwap and above_vwap and uptrend):
                return None
            
            # Calculate stops and targets
            atr = TechnicalIndicators.calculate_atr(daily_df) if daily_df is not None else current_price * 0.02
            
            if atr == 0:
                atr = current_price * 0.02
            
            stop_loss = vwap - (atr * 1.0)
            target = current_price + (atr * 2.5)
            
            # Calculate volatility percentile
            volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df) if daily_df is not None else 50.0
            
            # Volume analysis
            current_volume = intraday_df['volume'].iloc[-10:].mean() if len(intraday_df) >= 10 else intraday_df['volume'].iloc[-1]
            avg_volume = daily_df['volume'].mean() if daily_df is not None and not daily_df.empty else current_volume
            volume_surge = current_volume > avg_volume * 1.1
            
            # Use comprehensive 7-dimension scoring
            scores = ScoringEngine.calculate_composite_scores(
                daily_df=daily_df,
                intraday_df=intraday_df,
                entry_price=current_price,
                stop_loss=stop_loss,
                target_price=target,
                current_volume=current_volume,
                volume_surge=volume_surge,
                breakout_pct=0.0,  # Not a breakout, pullback
                volatility_percentile=volatility_percentile,
                sentiment_data=sentiment_data,
                min_avg_volume=self.config.MIN_AVG_VOLUME
            )
            
            return {
                'strategy': 'VWAP_PULLBACK',
                'entry_price': float(current_price),
                'stop_loss': float(stop_loss),
                'target_price': float(target),
                'conviction_score': scores['conviction_score'],
                'risk_score': scores['risk_score'],
                'features': {
                    'vwap': float(vwap),
                    'distance_from_vwap_pct': float(distance_from_vwap * 100),
                    'uptrend': uptrend,
                    'atr': float(atr),
                    'volatility_percentile': float(volatility_percentile)
                },
                'dimension_scores': scores['dimension_scores']
            }
        
        except Exception as e:
            print(f"VWAP analysis error for {symbol}: {e}")
            return None
