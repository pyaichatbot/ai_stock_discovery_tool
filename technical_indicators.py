"""
AI-Powered Stock Discovery Tool - Technical Indicators
"""

import numpy as np
import pandas as pd
from typing import Dict


class TechnicalIndicators:
    """Calculate technical indicators"""
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> float:
        """Volume-weighted average price"""
        if df is None or df.empty or 'close' not in df or 'volume' not in df:
            return 0.0
        
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        total_volume = df['volume'].sum()
        
        if total_volume == 0:
            return 0.0
        
        vwap = (typical_price * df['volume']).sum() / total_volume
        return float(vwap)
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
        """Average True Range"""
        if df is None or df.empty or len(df) < period:
            return 0.0
        
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate true range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Skip first value (has rolled data)
        tr = tr[1:]
        
        if len(tr) < period:
            return 0.0
        
        atr = np.mean(tr[-period:])
        return float(atr)
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
        """Relative Strength Index"""
        if df is None or df.empty or len(df) < period + 1:
            return 50.0
        
        close = df['close'].values
        delta = np.diff(close)
        
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame, short: int = 20, long: int = 50) -> Dict:
        """Calculate short and long MAs"""
        if df is None or df.empty:
            return {
                'ma_short': 0.0,
                'ma_long': 0.0,
                'ma_cross': False
            }
        
        close = df['close'].values
        
        ma_short = np.mean(close[-short:]) if len(close) >= short else close[-1]
        ma_long = np.mean(close[-long:]) if len(close) >= long else close[-1]
        
        return {
            'ma_short': float(ma_short),
            'ma_long': float(ma_long),
            'ma_cross': ma_short > ma_long
        }
    
    @staticmethod
    def calculate_volatility_percentile(df: pd.DataFrame, lookback: int = 60) -> float:
        """Calculate volatility percentile (for HVB mode)"""
        if df is None or df.empty or len(df) < lookback:
            return 50.0
        
        # Calculate daily returns
        close = df['close'].values
        returns = np.diff(close) / close[:-1]
        
        # Current volatility (last 20 days)
        current_vol = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
        
        # Historical volatility distribution
        rolling_vol = []
        for i in range(20, len(returns)):
            vol = np.std(returns[i-20:i])
            rolling_vol.append(vol)
        
        if not rolling_vol:
            return 50.0
        
        # Percentile rank
        percentile = (np.sum(np.array(rolling_vol) < current_vol) / len(rolling_vol)) * 100
        return float(percentile)
