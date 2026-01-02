"""
AI-Powered Stock Discovery Tool - Opening Range Breakout Strategy
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from config import Config
from technical_indicators import TechnicalIndicators
from scoring_engine import ScoringEngine


class OpeningRangeBreakout:
    """Opening Range Breakout (ORB) Strategy"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, symbol: str, intraday_df: pd.DataFrame, daily_df: pd.DataFrame, 
                sentiment_data: Optional[Dict] = None) -> Optional[Dict]:
        """Detect ORB setup"""
        if intraday_df is None or intraday_df.empty or len(intraday_df) < 15:
            return None
        
        try:
            # Get today's data
            if 'datetime' not in intraday_df.columns:
                return None
            
            # Ensure datetime column is proper datetime type
            intraday_df['datetime'] = pd.to_datetime(intraday_df['datetime'])
            
            # Get today's date (timezone naive)
            latest_dt = intraday_df['datetime'].max()
            today = latest_dt.date()
            
            # Filter to today's data
            today_data = intraday_df[intraday_df['datetime'].dt.date == today].copy()
            
            if len(today_data) < 15:
                return None
            
            # Sort by time
            today_data = today_data.sort_values('datetime')
            
            # Get opening range (first 15 minutes)
            opening_range = today_data.head(self.config.ORB_PERIOD_MINUTES)
            orb_high = opening_range['high'].max()
            orb_low = opening_range['low'].min()
            
            # Current price
            current_price = today_data['close'].iloc[-1]
            
            # Volume analysis
            current_volume = today_data['volume'].iloc[-10:].mean()
            avg_volume = daily_df['volume'].mean() if daily_df is not None and not daily_df.empty else current_volume
            
            volume_surge = current_volume > avg_volume * 1.2
            
            # Check for breakout above ORB high
            breakout_up = current_price > orb_high and volume_surge
            
            if not breakout_up:
                return None
            
            # Calculate stops and targets
            atr = TechnicalIndicators.calculate_atr(daily_df) if daily_df is not None else (orb_high - orb_low)
            
            if atr == 0:
                atr = (orb_high - orb_low)
            
            stop_loss = orb_high - (atr * 1.5)
            target = orb_high + (atr * 2.0)
            
            # Breakout strength
            breakout_pct = ((current_price - orb_high) / orb_high) * 100
            
            # Calculate volatility percentile
            volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df) if daily_df is not None else 50.0
            
            # Use comprehensive 7-dimension scoring
            scores = ScoringEngine.calculate_composite_scores(
                daily_df=daily_df,
                intraday_df=intraday_df,
                entry_price=current_price,
                stop_loss=max(stop_loss, orb_low),
                target_price=target,
                current_volume=current_volume,
                volume_surge=volume_surge,
                breakout_pct=breakout_pct,
                volatility_percentile=volatility_percentile,
                sentiment_data=sentiment_data,
                min_avg_volume=self.config.MIN_AVG_VOLUME
            )
            
            return {
                'strategy': 'ORB',
                'entry_price': float(current_price),
                'stop_loss': float(max(stop_loss, orb_low)),  # Stop not below ORB low
                'target_price': float(target),
                'conviction_score': scores['conviction_score'],
                'risk_score': scores['risk_score'],
                'features': {
                    'orb_high': float(orb_high),
                    'orb_low': float(orb_low),
                    'volume_surge': volume_surge,
                    'atr': float(atr),
                    'breakout_pct': float(breakout_pct),
                    'volatility_percentile': float(volatility_percentile)
                },
                'dimension_scores': scores['dimension_scores']
            }
        
        except Exception as e:
            print(f"ORB analysis error for {symbol}: {e}")
            return None
