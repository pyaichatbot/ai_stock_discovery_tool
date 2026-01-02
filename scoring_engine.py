"""
AI-Powered Stock Discovery Tool - Comprehensive Scoring Engine
Implements 7-dimension scoring system per PRD Section 7
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from technical_indicators import TechnicalIndicators


class ScoringEngine:
    """Calculate all 7 scoring dimensions for stock picks"""
    
    @staticmethod
    def calculate_trend_score(daily_df: pd.DataFrame, current_price: float) -> float:
        """
        Dimension 1: Trend Score
        Strength & direction of price trend (0-100)
        """
        if daily_df is None or daily_df.empty or len(daily_df) < 50:
            return 50.0  # Neutral
        
        close = daily_df['close'].values
        
        # Calculate multiple timeframe trends
        ma_20 = np.mean(close[-20:])
        ma_50 = np.mean(close[-50:]) if len(close) >= 50 else ma_20
        
        # Price vs MAs
        above_20 = current_price > ma_20
        above_50 = current_price > ma_50
        
        # Trend strength (distance from MAs)
        dist_from_20 = abs(current_price - ma_20) / ma_20 if ma_20 > 0 else 0
        dist_from_50 = abs(current_price - ma_50) / ma_50 if ma_50 > 0 else 0
        
        # MA alignment (bullish if 20 > 50)
        ma_alignment = 1.0 if ma_20 > ma_50 else -1.0
        
        # Score calculation
        base_score = 50.0
        
        if above_20 and above_50:
            base_score += 20  # Strong uptrend
        elif above_20:
            base_score += 10  # Moderate uptrend
        elif not above_20 and not above_50:
            base_score -= 20  # Strong downtrend
        else:
            base_score -= 10  # Moderate downtrend
        
        # Add alignment bonus
        base_score += ma_alignment * 10
        
        # Add distance bonus (stronger trend = higher score)
        base_score += min(10, dist_from_20 * 1000) if above_20 else -min(10, dist_from_20 * 1000)
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_momentum_score(daily_df: pd.DataFrame, current_price: float, 
                                breakout_pct: float = 0.0) -> float:
        """
        Dimension 2: Momentum Score
        Rate of change & breakout strength (0-100)
        """
        if daily_df is None or daily_df.empty or len(daily_df) < 20:
            return 50.0
        
        close = daily_df['close'].values
        
        # Rate of change (ROC)
        roc_5 = ((close[-1] - close[-5]) / close[-5]) * 100 if len(close) >= 5 else 0
        roc_10 = ((close[-1] - close[-10]) / close[-10]) * 100 if len(close) >= 10 else 0
        
        # RSI momentum
        rsi = TechnicalIndicators.calculate_rsi(daily_df)
        rsi_momentum = 0.0
        if 50 < rsi < 70:
            rsi_momentum = 20  # Healthy momentum
        elif rsi >= 70:
            rsi_momentum = 10  # Overbought but still momentum
        elif rsi < 30:
            rsi_momentum = -20  # Oversold, negative momentum
        
        # Breakout strength (if provided)
        breakout_score = min(30, abs(breakout_pct) * 10) if breakout_pct != 0 else 0
        
        # Combine ROC
        roc_score = (abs(roc_5) + abs(roc_10)) / 2
        roc_score = min(30, roc_score * 2)
        
        # Base score
        base_score = 50.0
        base_score += roc_score if roc_5 > 0 else -roc_score
        base_score += rsi_momentum
        base_score += breakout_score
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_volume_score(daily_df: pd.DataFrame, current_volume: float = None,
                              volume_surge: bool = False) -> float:
        """
        Dimension 3: Volume Score
        Participation & confirmation (0-100)
        """
        if daily_df is None or daily_df.empty:
            return 50.0
        
        volumes = daily_df['volume'].values
        avg_volume = np.mean(volumes)
        
        if current_volume is None:
            current_volume = volumes[-1] if len(volumes) > 0 else avg_volume
        
        if avg_volume == 0:
            return 50.0
        
        # Volume ratio
        volume_ratio = current_volume / avg_volume
        
        # Volume trend (recent vs older)
        if len(volumes) >= 20:
            recent_vol = np.mean(volumes[-5:])
            older_vol = np.mean(volumes[-20:-5])
            volume_trend = recent_vol / older_vol if older_vol > 0 else 1.0
        else:
            volume_trend = 1.0
        
        # Score calculation
        base_score = 50.0
        
        # Volume surge bonus
        if volume_surge or volume_ratio > 1.5:
            base_score += 25
        elif volume_ratio > 1.2:
            base_score += 15
        elif volume_ratio > 1.0:
            base_score += 5
        elif volume_ratio < 0.8:
            base_score -= 15  # Low volume penalty
        
        # Volume trend bonus
        if volume_trend > 1.1:
            base_score += 10
        elif volume_trend < 0.9:
            base_score -= 10
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_volatility_score(daily_df: pd.DataFrame, volatility_percentile: float = None) -> float:
        """
        Dimension 4: Volatility Score
        Risk & opportunity balance (0-100)
        Higher volatility = more opportunity but more risk
        Optimal range: 60-80th percentile
        """
        if daily_df is None or daily_df.empty:
            return 50.0
        
        # Calculate volatility percentile if not provided
        if volatility_percentile is None:
            volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df)
        
        # ATR as percentage of price
        atr = TechnicalIndicators.calculate_atr(daily_df)
        current_price = daily_df['close'].iloc[-1]
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
        
        # Score calculation
        # Optimal volatility: 60-80th percentile (good opportunity, manageable risk)
        base_score = 50.0
        
        if 60 <= volatility_percentile <= 80:
            base_score += 25  # Sweet spot
        elif 50 <= volatility_percentile < 60:
            base_score += 15  # Good
        elif 80 < volatility_percentile <= 90:
            base_score += 10  # High but acceptable
        elif volatility_percentile > 90:
            base_score -= 10  # Too volatile (risk)
        elif volatility_percentile < 30:
            base_score -= 15  # Too low (no opportunity)
        
        # ATR adjustment (normalize to 0-5% range)
        if 1.0 <= atr_pct <= 3.0:
            base_score += 10  # Good ATR range
        elif atr_pct > 5.0:
            base_score -= 15  # Too wide stops
        elif atr_pct < 0.5:
            base_score -= 10  # Too tight
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_sentiment_score(sentiment_data: Optional[Dict] = None) -> float:
        """
        Dimension 5: Sentiment Score
        News & event polarity (0-100)
        Will be enhanced with news integration
        """
        if sentiment_data is None:
            return 50.0  # Neutral (no news data)
        
        # Extract sentiment components
        polarity = sentiment_data.get('polarity', 0.0)  # -1 to +1
        confidence = sentiment_data.get('confidence', 0.5)  # 0 to 1
        
        # Convert polarity to 0-100 score
        base_score = 50.0 + (polarity * 50.0)
        
        # Adjust by confidence
        base_score = base_score * confidence + 50.0 * (1 - confidence)
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_liquidity_score(daily_df: pd.DataFrame, min_avg_volume: int = 100000) -> float:
        """
        Dimension 6: Liquidity Score
        Slippage & execution realism (0-100)
        """
        if daily_df is None or daily_df.empty:
            return 0.0  # No data = no liquidity
        
        volumes = daily_df['volume'].values
        avg_volume = np.mean(volumes)
        current_price = daily_df['close'].iloc[-1]
        
        # Average daily value traded
        avg_value = avg_volume * current_price
        
        # Score based on liquidity thresholds
        base_score = 0.0
        
        if avg_volume >= min_avg_volume * 5:
            base_score = 100.0  # Excellent liquidity
        elif avg_volume >= min_avg_volume * 3:
            base_score = 85.0  # Very good
        elif avg_volume >= min_avg_volume * 2:
            base_score = 70.0  # Good
        elif avg_volume >= min_avg_volume * 1.5:
            base_score = 60.0  # Acceptable
        elif avg_volume >= min_avg_volume:
            base_score = 50.0  # Minimum
        else:
            base_score = 30.0  # Low liquidity
        
        # Value traded bonus (higher value = better execution)
        if avg_value >= 10_000_000:  # 10M+ daily value
            base_score = min(100.0, base_score + 10)
        elif avg_value >= 5_000_000:  # 5M+ daily value
            base_score = min(100.0, base_score + 5)
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_risk_score(daily_df: pd.DataFrame, entry_price: float, 
                            stop_loss: float, target_price: float,
                            volatility_percentile: float = None) -> float:
        """
        Dimension 7: Risk Score
        Drawdown & failure modes (0-100, higher = more risk)
        """
        if daily_df is None or daily_df.empty:
            return 50.0
        
        # Risk/Reward ratio
        risk_amount = abs(entry_price - stop_loss)
        reward_amount = abs(target_price - entry_price)
        rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Stop loss distance (%)
        sl_distance_pct = (risk_amount / entry_price) * 100 if entry_price > 0 else 0
        
        # Volatility percentile (if provided)
        if volatility_percentile is None:
            volatility_percentile = TechnicalIndicators.calculate_volatility_percentile(daily_df)
        
        # Recent drawdown
        close = daily_df['close'].values
        if len(close) >= 20:
            recent_high = np.max(close[-20:])
            current = close[-1]
            drawdown_pct = ((recent_high - current) / recent_high) * 100 if recent_high > 0 else 0
        else:
            drawdown_pct = 0
        
        # Base risk score (starts at 50 = medium risk)
        base_score = 50.0
        
        # R:R ratio adjustment (better R:R = lower risk)
        if rr_ratio >= 3.0:
            base_score -= 20  # Excellent R:R
        elif rr_ratio >= 2.0:
            base_score -= 10  # Good R:R
        elif rr_ratio >= 1.5:
            base_score -= 5  # Acceptable R:R
        elif rr_ratio < 1.0:
            base_score += 15  # Poor R:R = higher risk
        
        # Stop loss distance (too tight = higher risk of stop-out)
        if sl_distance_pct < 1.0:
            base_score += 20  # Very tight stop = high risk
        elif sl_distance_pct < 2.0:
            base_score += 10  # Tight stop
        elif sl_distance_pct > 5.0:
            base_score -= 5  # Wide stop = lower risk of stop-out
        
        # Volatility adjustment
        if volatility_percentile > 90:
            base_score += 15  # High volatility = higher risk
        elif volatility_percentile > 80:
            base_score += 10
        elif volatility_percentile < 30:
            base_score -= 5  # Low volatility = lower risk
        
        # Drawdown adjustment
        if drawdown_pct > 10:
            base_score += 10  # High drawdown = higher risk
        elif drawdown_pct > 5:
            base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    @staticmethod
    def calculate_composite_scores(daily_df: pd.DataFrame, intraday_df: Optional[pd.DataFrame],
                                  entry_price: float, stop_loss: float, target_price: float,
                                  current_volume: float = None, volume_surge: bool = False,
                                  breakout_pct: float = 0.0, volatility_percentile: float = None,
                                  sentiment_data: Optional[Dict] = None,
                                  min_avg_volume: int = 100000) -> Dict[str, float]:
        """
        Calculate all 7 dimension scores and composite conviction/risk scores
        
        Returns:
            Dict with all scores:
            - trend_score, momentum_score, volume_score, volatility_score
            - sentiment_score, liquidity_score, risk_score
            - conviction_score (composite), risk_score (composite)
        """
        # Calculate all 7 dimensions
        trend = ScoringEngine.calculate_trend_score(daily_df, entry_price)
        momentum = ScoringEngine.calculate_momentum_score(daily_df, entry_price, breakout_pct)
        volume = ScoringEngine.calculate_volume_score(daily_df, current_volume, volume_surge)
        volatility = ScoringEngine.calculate_volatility_score(daily_df, volatility_percentile)
        sentiment = ScoringEngine.calculate_sentiment_score(sentiment_data)
        liquidity = ScoringEngine.calculate_liquidity_score(daily_df, min_avg_volume)
        risk = ScoringEngine.calculate_risk_score(daily_df, entry_price, stop_loss, target_price, volatility_percentile)
        
        # Composite Conviction Score (weighted average)
        # Higher weight on trend, momentum, volume (core technicals)
        # Lower weight on sentiment (may not always be available)
        weights = {
            'trend': 0.20,
            'momentum': 0.20,
            'volume': 0.15,
            'volatility': 0.15,
            'sentiment': 0.10,  # Lower weight (may be neutral if no news)
            'liquidity': 0.10,
            'risk': 0.10  # Inverted (lower risk = higher conviction)
        }
        
        # Risk score is inverted for conviction (lower risk = higher conviction)
        risk_inverted = 100.0 - risk
        
        conviction = (
            trend * weights['trend'] +
            momentum * weights['momentum'] +
            volume * weights['volume'] +
            volatility * weights['volatility'] +
            sentiment * weights['sentiment'] +
            liquidity * weights['liquidity'] +
            risk_inverted * weights['risk']
        )
        
        return {
            'trend_score': trend,
            'momentum_score': momentum,
            'volume_score': volume,
            'volatility_score': volatility,
            'sentiment_score': sentiment,
            'liquidity_score': liquidity,
            'risk_score': risk,
            'conviction_score': max(0.0, min(100.0, conviction)),
            'dimension_scores': {
                'trend': trend,
                'momentum': momentum,
                'volume': volume,
                'volatility': volatility,
                'sentiment': sentiment,
                'liquidity': liquidity,
                'risk': risk
            }
        }

