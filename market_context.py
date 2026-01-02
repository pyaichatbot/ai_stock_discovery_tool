"""
AI-Powered Stock Discovery Tool - Market Context Analysis
Index confirmation, sector analysis, relative strength
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from data_fetcher import MarketDataFetcher


class MarketContext:
    """Analyze market context: index trends, sector strength, relative strength"""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.index_symbol = "^NSEI"  # NIFTY 50 index
    
    def get_index_trend(self) -> str:
        """Get index trend (bullish/bearish/neutral)"""
        return self.fetcher.get_index_trend()
    
    def calculate_relative_strength(self, symbol: str, lookback_days: int = 20) -> Optional[float]:
        """
        Calculate relative strength vs NIFTY index
        
        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back
        
        Returns:
            Relative strength ratio (stock return / index return)
            > 1.0 means stock outperforming index
            < 1.0 means stock underperforming index
        """
        try:
            # Get stock data
            stock_df = self.fetcher.get_stock_data(symbol, period=f"{lookback_days + 5}d", interval="1d")
            if stock_df is None or len(stock_df) < lookback_days:
                return None
            
            # Get index data
            index_df = self.fetcher.get_stock_data(self.index_symbol, period=f"{lookback_days + 5}d", interval="1d")
            if index_df is None or len(index_df) < lookback_days:
                return None
            
            # Calculate returns
            stock_start = stock_df['close'].iloc[-lookback_days]
            stock_end = stock_df['close'].iloc[-1]
            stock_return = (stock_end - stock_start) / stock_start if stock_start > 0 else 0
            
            index_start = index_df['close'].iloc[-lookback_days]
            index_end = index_df['close'].iloc[-1]
            index_return = (index_end - index_start) / index_start if index_start > 0 else 0
            
            # Relative strength
            if index_return == 0:
                return 1.0  # Neutral if index didn't move
            
            relative_strength = stock_return / index_return if index_return != 0 else 1.0
            return float(relative_strength)
        
        except Exception as e:
            return None
    
    def is_index_aligned(self, symbol: str, min_relative_strength: float = 1.0) -> bool:
        """
        Check if stock is aligned with index (outperforming or at least keeping pace)
        
        Args:
            symbol: Stock symbol
            min_relative_strength: Minimum relative strength required (default 1.0 = at least matching index)
        
        Returns:
            True if stock is aligned with index
        """
        rs = self.calculate_relative_strength(symbol)
        if rs is None:
            return True  # If can't calculate, assume aligned (don't filter out)
        return rs >= min_relative_strength
    
    def get_sector_strength(self, symbols: list, sector_symbols: list = None) -> Dict:
        """
        Calculate sector strength based on multiple stocks in sector
        
        Args:
            symbols: List of stock symbols in sector
            sector_symbols: Optional list of sector symbols (if None, uses provided symbols)
        
        Returns:
            Dict with sector strength metrics
        """
        if sector_symbols is None:
            sector_symbols = symbols
        
        if not sector_symbols:
            return {
                'strength': 0.5,  # Neutral
                'trend': 'neutral',
                'avg_relative_strength': 1.0
            }
        
        # Calculate relative strength for each symbol in sector
        rs_values = []
        for symbol in sector_symbols[:10]:  # Limit to 10 to avoid too many API calls
            rs = self.calculate_relative_strength(symbol)
            if rs is not None:
                rs_values.append(rs)
        
        if not rs_values:
            return {
                'strength': 0.5,
                'trend': 'neutral',
                'avg_relative_strength': 1.0
            }
        
        avg_rs = np.mean(rs_values)
        
        # Determine strength
        if avg_rs >= 1.2:
            strength = 0.8
            trend = 'strong'
        elif avg_rs >= 1.1:
            strength = 0.7
            trend = 'bullish'
        elif avg_rs >= 1.0:
            strength = 0.6
            trend = 'moderate'
        elif avg_rs >= 0.9:
            strength = 0.4
            trend = 'weak'
        else:
            strength = 0.2
            trend = 'bearish'
        
        return {
            'strength': float(strength),
            'trend': trend,
            'avg_relative_strength': float(avg_rs),
            'sample_size': len(rs_values)
        }
    
    def check_index_confirmation(self, symbol: str, index_trend: str = None) -> Dict:
        """
        Check if stock setup is confirmed by index trend
        
        Args:
            symbol: Stock symbol
            index_trend: Index trend (bullish/bearish/neutral), if None will fetch
        
        Returns:
            Dict with confirmation status and relative strength
        """
        if index_trend is None:
            index_trend = self.get_index_trend()
        
        relative_strength = self.calculate_relative_strength(symbol)
        
        # For bullish setups, want bullish index and positive relative strength
        # For bearish setups, want bearish index (but we focus on bullish setups)
        confirmed = False
        if index_trend == 'bullish':
            if relative_strength is None:
                confirmed = True  # Assume confirmed if can't calculate
            else:
                confirmed = relative_strength >= 0.95  # At least keeping pace
        elif index_trend == 'neutral':
            confirmed = True  # Neutral is acceptable
        else:  # bearish
            # In bearish market, only take strongest stocks
            if relative_strength is None:
                confirmed = False
            else:
                confirmed = relative_strength >= 1.1  # Must significantly outperform
        
        return {
            'confirmed': confirmed,
            'index_trend': index_trend,
            'relative_strength': relative_strength,
            'reason': f"Index: {index_trend}, RS: {relative_strength:.2f}" if relative_strength else f"Index: {index_trend}, RS: N/A"
        }
    
    def is_circuit_breaker_hit(self, symbol: str) -> bool:
        """
        Check if stock hit circuit breaker (trading halt)
        
        India market circuit breakers:
        - 10% move → 15-minute halt
        - 15% move → 45-minute halt
        - 20% move → Rest of day halt
        
        Args:
            symbol: Stock symbol
        
        Returns:
            True if circuit breaker likely hit, False otherwise
        """
        try:
            # Get recent price data
            stock_df = self.fetcher.get_stock_data(symbol, period="2d", interval="1d")
            if stock_df is None or len(stock_df) < 2:
                return False
            
            current_price = stock_df['close'].iloc[-1]
            previous_close = stock_df['close'].iloc[-2] if len(stock_df) >= 2 else stock_df['close'].iloc[0]
            
            if previous_close <= 0:
                return False
            
            # Calculate percentage move
            price_change_pct = abs((current_price - previous_close) / previous_close) * 100
            
            # Check if move exceeds circuit breaker thresholds
            # If move > 10%, likely hit circuit breaker
            if price_change_pct >= 10.0:
                # Additional check: if price hasn't changed in last few minutes, likely halted
                # For daily data, if current == previous and move was large, likely halted
                if abs(current_price - previous_close) < 0.01 and price_change_pct >= 10.0:
                    return True
                # If move is exactly 10%, 15%, or 20%, likely circuit breaker
                if price_change_pct in [10.0, 15.0, 20.0]:
                    return True
            
            return False
        
        except Exception as e:
            # If check fails, assume no circuit breaker (don't block scanning)
            return False
    
    def is_near_circuit_breaker(self, symbol: str, threshold_pct: float = 8.0) -> bool:
        """
        Check if stock is near circuit breaker threshold
        
        Args:
            symbol: Stock symbol
            threshold_pct: Percentage move threshold (default 8%)
        
        Returns:
            True if near circuit breaker, False otherwise
        """
        try:
            stock_df = self.fetcher.get_stock_data(symbol, period="2d", interval="1d")
            if stock_df is None or len(stock_df) < 2:
                return False
            
            current_price = stock_df['close'].iloc[-1]
            previous_close = stock_df['close'].iloc[-2] if len(stock_df) >= 2 else stock_df['close'].iloc[0]
            
            if previous_close <= 0:
                return False
            
            price_change_pct = abs((current_price - previous_close) / previous_close) * 100
            
            # Near circuit breaker if move is 8-9% (approaching 10% threshold)
            return threshold_pct <= price_change_pct < 10.0
        
        except Exception:
            return False

