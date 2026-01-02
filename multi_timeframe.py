"""
Multi-Timeframe Analysis - Check daily/weekly/monthly alignment
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

from data_fetcher import MarketDataFetcher
from technical_indicators import TechnicalIndicators


class MultiTimeframeAnalyzer:
    """Analyze stocks across multiple timeframes"""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
    
    def analyze(self, symbol: str) -> Dict:
        """
        Analyze symbol across daily, weekly, and monthly timeframes
        
        Returns:
            Dict with trend, alignment, and support/resistance levels
        """
        result = {
            'symbol': symbol,
            'daily': None,
            'weekly': None,
            'monthly': None,
            'alignment': 'none',
            'alignment_strength': 0.0,
            'support_levels': [],
            'resistance_levels': []
        }
        
        # Daily analysis
        daily_df = self.fetcher.get_stock_data(symbol, period="60d", interval="1d")
        if daily_df is not None and len(daily_df) >= 20:
            result['daily'] = self._analyze_timeframe(daily_df, 'daily')
        
        # Weekly analysis
        weekly_df = self.fetcher.get_stock_data(symbol, period="2y", interval="1wk")
        if weekly_df is not None and len(weekly_df) >= 20:
            result['weekly'] = self._analyze_timeframe(weekly_df, 'weekly')
        
        # Monthly analysis
        monthly_df = self.fetcher.get_stock_data(symbol, period="5y", interval="1mo")
        if monthly_df is not None and len(monthly_df) >= 20:
            result['monthly'] = self._analyze_timeframe(monthly_df, 'monthly')
        
        # Calculate alignment
        result['alignment'], result['alignment_strength'] = self._calculate_alignment(
            result['daily'],
            result['weekly'],
            result['monthly']
        )
        
        # Calculate support/resistance levels
        result['support_levels'], result['resistance_levels'] = self._calculate_levels(
            daily_df if daily_df is not None else None,
            weekly_df if weekly_df is not None else None,
            monthly_df if monthly_df is not None else None
        )
        
        return result
    
    def _analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze a single timeframe"""
        if df is None or len(df) < 20:
            return None
        
        current_price = df['close'].iloc[-1]
        
        # Calculate MAs
        ma_20 = df['close'].rolling(20).mean().iloc[-1]
        ma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else None
        
        # Trend determination
        if ma_50:
            if current_price > ma_20 > ma_50:
                trend = 'bullish'
            elif current_price < ma_20 < ma_50:
                trend = 'bearish'
            else:
                trend = 'neutral'
        else:
            if current_price > ma_20:
                trend = 'bullish'
            elif current_price < ma_20:
                trend = 'bearish'
            else:
                trend = 'neutral'
        
        # Momentum
        rsi = TechnicalIndicators.calculate_rsi(df)
        
        # Price position relative to range
        high_52w = df['high'].tail(252).max() if len(df) >= 252 else df['high'].max()
        low_52w = df['low'].tail(252).min() if len(df) >= 252 else df['low'].min()
        price_position = ((current_price - low_52w) / (high_52w - low_52w) * 100) if (high_52w - low_52w) > 0 else 50.0
        
        return {
            'timeframe': timeframe,
            'current_price': float(current_price),
            'trend': trend,
            'ma_20': float(ma_20),
            'ma_50': float(ma_50) if ma_50 else None,
            'rsi': float(rsi),
            'price_position': float(price_position),
            'high_52w': float(high_52w),
            'low_52w': float(low_52w)
        }
    
    def _calculate_alignment(
        self,
        daily: Optional[Dict],
        weekly: Optional[Dict],
        monthly: Optional[Dict]
    ) -> Tuple[str, float]:
        """Calculate alignment strength across timeframes"""
        trends = []
        
        if daily and daily.get('trend'):
            trends.append(daily['trend'])
        if weekly and weekly.get('trend'):
            trends.append(weekly['trend'])
        if monthly and monthly.get('trend'):
            trends.append(monthly['trend'])
        
        if not trends:
            return 'none', 0.0
        
        # Count bullish/bearish/neutral
        bullish_count = trends.count('bullish')
        bearish_count = trends.count('bearish')
        neutral_count = trends.count('neutral')
        
        total = len(trends)
        
        # Perfect alignment
        if bullish_count == total:
            return 'bullish', 1.0
        elif bearish_count == total:
            return 'bearish', 1.0
        elif neutral_count == total:
            return 'neutral', 0.5
        
        # Partial alignment
        if bullish_count > bearish_count and bullish_count > neutral_count:
            strength = bullish_count / total
            return 'bullish', strength
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            strength = bearish_count / total
            return 'bearish', strength
        else:
            return 'neutral', 0.5
    
    def _calculate_levels(
        self,
        daily_df: Optional[pd.DataFrame],
        weekly_df: Optional[pd.DataFrame],
        monthly_df: Optional[pd.DataFrame]
    ) -> Tuple[list, list]:
        """Calculate support and resistance levels from higher timeframes"""
        support_levels = []
        resistance_levels = []
        
        # Use weekly and monthly for key levels
        for df, timeframe in [(weekly_df, 'weekly'), (monthly_df, 'monthly')]:
            if df is None or len(df) < 20:
                continue
            
            # Recent highs and lows
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            
            # Moving averages as support/resistance
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else None
            
            # Add levels
            resistance_levels.append({
                'level': float(recent_high),
                'timeframe': timeframe,
                'type': 'recent_high'
            })
            
            support_levels.append({
                'level': float(recent_low),
                'timeframe': timeframe,
                'type': 'recent_low'
            })
            
            support_levels.append({
                'level': float(ma_20),
                'timeframe': timeframe,
                'type': 'ma_20'
            })
            
            if ma_50:
                support_levels.append({
                    'level': float(ma_50),
                    'timeframe': timeframe,
                    'type': 'ma_50'
                })
        
        # Sort and deduplicate
        support_levels = sorted(support_levels, key=lambda x: x['level'], reverse=True)
        resistance_levels = sorted(resistance_levels, key=lambda x: x['level'], reverse=True)
        
        return support_levels[:5], resistance_levels[:5]
    
    def format_analysis(self, analysis: Dict) -> str:
        """Format multi-timeframe analysis for display"""
        lines = []
        lines.append("📊 Multi-Timeframe Analysis:")
        
        # Daily
        if analysis['daily']:
            d = analysis['daily']
            trend_icon = '🟢' if d['trend'] == 'bullish' else '🔴' if d['trend'] == 'bearish' else '🟡'
            lines.append(f"   Daily:   {d['trend'].upper():8} {trend_icon} | RSI: {d['rsi']:.1f} | Price: ₹{d['current_price']:.2f}")
        
        # Weekly
        if analysis['weekly']:
            w = analysis['weekly']
            trend_icon = '🟢' if w['trend'] == 'bullish' else '🔴' if w['trend'] == 'bearish' else '🟡'
            lines.append(f"   Weekly:  {w['trend'].upper():8} {trend_icon} | RSI: {w['rsi']:.1f} | Price: ₹{w['current_price']:.2f}")
        
        # Monthly
        if analysis['monthly']:
            m = analysis['monthly']
            trend_icon = '🟢' if m['trend'] == 'bullish' else '🔴' if m['trend'] == 'bearish' else '🟡'
            lines.append(f"   Monthly: {m['trend'].upper():8} {trend_icon} | RSI: {m['rsi']:.1f} | Price: ₹{m['current_price']:.2f}")
        
        # Alignment
        alignment = analysis['alignment']
        strength = analysis['alignment_strength']
        if alignment == 'bullish':
            alignment_icon = '✅' if strength >= 0.8 else '⚠️'
            lines.append(f"   → Alignment: {alignment.upper()} {alignment_icon} (Strength: {strength*100:.0f}%)")
        elif alignment == 'bearish':
            alignment_icon = '❌' if strength >= 0.8 else '⚠️'
            lines.append(f"   → Alignment: {alignment.upper()} {alignment_icon} (Strength: {strength*100:.0f}%)")
        else:
            lines.append(f"   → Alignment: {alignment.upper()} ⚠️ (Strength: {strength*100:.0f}%)")
        
        # Key levels
        if analysis['support_levels']:
            nearest_support = analysis['support_levels'][0]
            lines.append(f"   → Nearest Support: ₹{nearest_support['level']:.2f} ({nearest_support['timeframe']})")
        
        if analysis['resistance_levels']:
            nearest_resistance = analysis['resistance_levels'][0]
            lines.append(f"   → Nearest Resistance: ₹{nearest_resistance['level']:.2f} ({nearest_resistance['timeframe']})")
        
        return "\n".join(lines)

