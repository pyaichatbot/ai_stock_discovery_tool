"""
AI-Powered Stock Discovery Tool - Fundamental Analysis Module
Analyzes fundamental metrics (P/E, P/B, Debt, Revenue, etc.) before picking stocks
"""

import yfinance as yf
from typing import Dict, Optional
import numpy as np


class FundamentalAnalyzer:
    """Analyze fundamental metrics for stocks"""
    
    def __init__(self):
        self.cache = {}  # symbol -> (timestamp, data)
    
    def analyze(self, symbol: str) -> Dict:
        """
        Analyze fundamental metrics for a stock
        
        Returns:
            Dict with:
            - 'allowed': bool (should we pick this stock?)
            - 'fundamental_score': float (0-100)
            - 'metrics': dict (P/E, P/B, debt, etc.)
            - 'reason': str (why allowed/not allowed)
        """
        try:
            # Fetch fundamental data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or len(info) < 5:  # Insufficient data
                return {
                    'allowed': True,  # Don't block if data unavailable
                    'fundamental_score': 50.0,
                    'metrics': {},
                    'reason': 'Fundamental data unavailable, allowing based on technicals only'
                }
            
            # Extract key metrics
            metrics = self._extract_metrics(info)
            
            # Calculate fundamental score
            fundamental_score = self._calculate_fundamental_score(metrics)
            
            # Determine if we should allow this stock
            allowed, reason = self._should_allow(metrics, fundamental_score)
            
            return {
                'allowed': allowed,
                'fundamental_score': fundamental_score,
                'metrics': metrics,
                'reason': reason
            }
        
        except Exception as e:
            # If fundamental analysis fails, don't block the stock
            # (fallback to technical-only)
            return {
                'allowed': True,
                'fundamental_score': 50.0,
                'metrics': {},
                'reason': f'Fundamental analysis error: {str(e)[:50]}, allowing based on technicals'
            }
    
    def _extract_metrics(self, info: Dict) -> Dict:
        """Extract key fundamental metrics from yfinance info"""
        metrics = {}
        
        # Valuation metrics
        metrics['pe_ratio'] = info.get('trailingPE') or info.get('forwardPE')
        metrics['pb_ratio'] = info.get('priceToBook')
        metrics['peg_ratio'] = info.get('pegRatio')
        
        # Financial health
        metrics['debt_to_equity'] = info.get('debtToEquity')
        metrics['current_ratio'] = info.get('currentRatio')
        metrics['quick_ratio'] = info.get('quickRatio')
        
        # Profitability
        metrics['roe'] = info.get('returnOnEquity')  # Return on Equity
        metrics['roa'] = info.get('returnOnAssets')  # Return on Assets
        metrics['profit_margin'] = info.get('profitMargins')
        metrics['operating_margin'] = info.get('operatingMargins')
        
        # Growth
        metrics['revenue_growth'] = info.get('revenueGrowth')
        metrics['earnings_growth'] = info.get('earningsGrowth')
        metrics['earnings_quarterly_growth'] = info.get('earningsQuarterlyGrowth')
        
        # Financial strength
        metrics['total_cash'] = info.get('totalCash')
        metrics['total_debt'] = info.get('totalDebt')
        metrics['free_cashflow'] = info.get('freeCashflow')
        
        # Market cap
        metrics['market_cap'] = info.get('marketCap')
        
        # Earnings quality
        metrics['earnings_per_share'] = info.get('trailingEps') or info.get('forwardEps')
        
        # Sector/Industry for comparison
        metrics['sector'] = info.get('sector', '')
        metrics['industry'] = info.get('industry', '')
        
        return metrics
    
    def _calculate_fundamental_score(self, metrics: Dict) -> float:
        """
        Calculate fundamental score (0-100)
        Higher score = better fundamentals
        """
        score = 50.0  # Start neutral
        factors = []
        
        # 1. Valuation (P/E, P/B) - 20 points
        pe = metrics.get('pe_ratio')
        pb = metrics.get('pb_ratio')
        
        if pe is not None and pe > 0:
            # P/E < 15: +10, 15-25: +5, 25-35: 0, >35: -5
            if pe < 15:
                score += 10
                factors.append('Low P/E')
            elif pe < 25:
                score += 5
                factors.append('Reasonable P/E')
            elif pe > 35:
                score -= 5
                factors.append('High P/E')
        
        if pb is not None and pb > 0:
            # P/B < 2: +10, 2-4: +5, >4: -5
            if pb < 2:
                score += 10
                factors.append('Low P/B')
            elif pb < 4:
                score += 5
            elif pb > 4:
                score -= 5
                factors.append('High P/B')
        
        # 2. Financial Health (Debt, Liquidity) - 20 points
        debt_to_equity = metrics.get('debt_to_equity')
        if debt_to_equity is not None:
            # Low debt (<0.5): +10, Moderate (0.5-1.5): +5, High (>1.5): -10
            if debt_to_equity < 0.5:
                score += 10
                factors.append('Low debt')
            elif debt_to_equity < 1.5:
                score += 5
            elif debt_to_equity > 1.5:
                score -= 10
                factors.append('High debt')
        
        current_ratio = metrics.get('current_ratio')
        if current_ratio is not None:
            # Good liquidity (>1.5): +5, Poor (<1): -5
            if current_ratio > 1.5:
                score += 5
                factors.append('Good liquidity')
            elif current_ratio < 1.0:
                score -= 5
                factors.append('Poor liquidity')
        
        # 3. Profitability (ROE, ROA, Margins) - 25 points
        roe = metrics.get('roe')
        if roe is not None:
            # ROE > 15%: +10, 10-15%: +5, <10%: -5
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > 15:
                score += 10
                factors.append('Strong ROE')
            elif roe_pct > 10:
                score += 5
            elif roe_pct < 5:
                score -= 5
                factors.append('Weak ROE')
        
        roa = metrics.get('roa')
        if roa is not None:
            # ROA > 5%: +5, <2%: -5
            roa_pct = roa * 100 if roa < 1 else roa
            if roa_pct > 5:
                score += 5
            elif roa_pct < 2:
                score -= 5
        
        profit_margin = metrics.get('profit_margin')
        if profit_margin is not None:
            # Margin > 10%: +5, <5%: -5
            margin_pct = profit_margin * 100 if profit_margin < 1 else profit_margin
            if margin_pct > 10:
                score += 5
                factors.append('Good margins')
            elif margin_pct < 5:
                score -= 5
        
        # 4. Growth (Revenue, Earnings) - 20 points
        revenue_growth = metrics.get('revenue_growth')
        if revenue_growth is not None:
            # Growth > 10%: +10, 5-10%: +5, <0%: -10
            growth_pct = revenue_growth * 100 if revenue_growth < 1 else revenue_growth
            if growth_pct > 10:
                score += 10
                factors.append('Strong revenue growth')
            elif growth_pct > 5:
                score += 5
            elif growth_pct < 0:
                score -= 10
                factors.append('Declining revenue')
        
        earnings_growth = metrics.get('earnings_growth')
        if earnings_growth is not None:
            # Growth > 10%: +5, <0%: -5
            growth_pct = earnings_growth * 100 if earnings_growth < 1 else earnings_growth
            if growth_pct > 10:
                score += 5
                factors.append('Earnings growth')
            elif growth_pct < 0:
                score -= 5
        
        # 5. Financial Strength (Cash, FCF) - 15 points
        free_cashflow = metrics.get('free_cashflow')
        if free_cashflow is not None and free_cashflow > 0:
            score += 5
            factors.append('Positive FCF')
        elif free_cashflow is not None and free_cashflow < 0:
            score -= 5
            factors.append('Negative FCF')
        
        # Normalize to 0-100
        score = max(0, min(100, score))
        
        return round(score, 1)
    
    def _should_allow(self, metrics: Dict, fundamental_score: float) -> tuple[bool, str]:
        """
        Determine if stock should be allowed based on fundamentals
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Hard filters - always reject
        debt_to_equity = metrics.get('debt_to_equity')
        # Note: D/E ratios vary by sector:
        # - Financial companies: 10-20+ is normal (leverage is part of business)
        # - IT companies: 5-15 can be acceptable (operating leases, etc.)
        # - Manufacturing: 0.5-2.0 is typical
        # We use a high threshold (20) to catch only extreme cases
        if debt_to_equity is not None and debt_to_equity > 20.0:
            return False, f'Excessive debt (D/E: {debt_to_equity:.2f})'
        
        # Negative earnings (P/E would be negative)
        pe = metrics.get('pe_ratio')
        if pe is not None and pe < 0:
            return False, 'Negative earnings (loss-making company)'
        
        # Very poor liquidity
        current_ratio = metrics.get('current_ratio')
        if current_ratio is not None and current_ratio < 0.5:
            return False, f'Poor liquidity (Current Ratio: {current_ratio:.2f})'
        
        # Declining revenue with negative margins
        revenue_growth = metrics.get('revenue_growth')
        profit_margin = metrics.get('profit_margin')
        if revenue_growth is not None and profit_margin is not None:
            revenue_growth_pct = revenue_growth * 100 if revenue_growth < 1 else revenue_growth
            margin_pct = profit_margin * 100 if profit_margin < 1 else profit_margin
            if revenue_growth_pct < -10 and margin_pct < 0:
                return False, f'Severe decline (Revenue: {revenue_growth_pct:.1f}%, Margin: {margin_pct:.1f}%)'
        
        # Score-based filter (optional - can be configurable)
        # For now, allow if score > 30 (very lenient)
        if fundamental_score < 30:
            return False, f'Poor fundamentals (Score: {fundamental_score:.1f}/100)'
        
        # All checks passed
        return True, f'Fundamentals OK (Score: {fundamental_score:.1f}/100)'
    
    def get_metrics_summary(self, metrics: Dict) -> str:
        """Get human-readable summary of fundamental metrics"""
        parts = []
        
        pe = metrics.get('pe_ratio')
        if pe:
            parts.append(f"P/E: {pe:.1f}")
        
        pb = metrics.get('pb_ratio')
        if pb:
            parts.append(f"P/B: {pb:.2f}")
        
        debt_to_equity = metrics.get('debt_to_equity')
        if debt_to_equity is not None:
            parts.append(f"D/E: {debt_to_equity:.2f}")
        
        roe = metrics.get('roe')
        if roe is not None:
            roe_pct = roe * 100 if roe < 1 else roe
            parts.append(f"ROE: {roe_pct:.1f}%")
        
        revenue_growth = metrics.get('revenue_growth')
        if revenue_growth is not None:
            growth_pct = revenue_growth * 100 if revenue_growth < 1 else revenue_growth
            parts.append(f"Rev Growth: {growth_pct:.1f}%")
        
        return " | ".join(parts) if parts else "N/A"

