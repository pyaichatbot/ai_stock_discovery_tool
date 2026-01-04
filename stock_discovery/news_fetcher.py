"""
AI-Powered Stock Discovery Tool - News & Event Fetcher
Uses Google News RSS (free, no subscription required)
"""

import feedparser
import re
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time


class NewsFetcher:
    """Fetch news and calculate sentiment for stocks"""
    
    # Sentiment keywords (simple keyword-based approach, no LLM needed)
    POSITIVE_KEYWORDS = [
        'profit', 'growth', 'surge', 'gain', 'rise', 'up', 'beat', 'exceed',
        'positive', 'strong', 'bullish', 'upgrade', 'buy', 'outperform',
        'earnings beat', 'guidance raise', 'expansion', 'acquisition'
    ]
    
    NEGATIVE_KEYWORDS = [
        'loss', 'decline', 'fall', 'down', 'miss', 'below', 'negative',
        'weak', 'bearish', 'downgrade', 'sell', 'underperform',
        'earnings miss', 'guidance cut', 'layoff', 'bankruptcy', 'fraud'
    ]
    
    EARNINGS_KEYWORDS = [
        'earnings', 'results', 'quarterly', 'q1', 'q2', 'q3', 'q4',
        'financial results', 'revenue', 'profit', 'eps'
    ]
    
    def __init__(self, cache_duration_minutes: int = 30):
        """
        Initialize news fetcher
        
        Args:
            cache_duration_minutes: How long to cache news (default 30 min)
        """
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self._cache = {}  # symbol -> (timestamp, news_data)
    
    def get_stock_news(self, symbol: str, max_articles: int = 10) -> List[Dict]:
        """
        Fetch recent news for a stock using Google News RSS
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE' or 'RELIANCE.NS')
            max_articles: Maximum number of articles to fetch
        
        Returns:
            List of news articles with title, link, published date, summary
        """
        # Clean symbol (remove .NS suffix for search)
        search_symbol = symbol.replace('.NS', '').upper()
        
        # Check cache
        cache_key = search_symbol
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            # Google News RSS URL
            # Search for stock symbol + "stock" or "share" to get relevant news
            from urllib.parse import quote_plus
            query = f"{search_symbol} stock India"
            encoded_query = quote_plus(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            articles = []
            for entry in feed.entries[:max_articles]:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('title', ''))
                }
                articles.append(article)
            
            # Cache results
            self._cache[cache_key] = (datetime.now(), articles)
            
            return articles
        
        except Exception as e:
            print(f"⚠️  News fetch error for {symbol}: {e}")
            return []
    
    def calculate_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Calculate sentiment from news articles using keyword matching
        
        Args:
            articles: List of news article dicts
        
        Returns:
            Dict with polarity (-1 to +1), confidence (0 to 1), and summary
        """
        if not articles:
            return {
                'polarity': 0.0,
                'confidence': 0.0,
                'summary': 'No news available',
                'article_count': 0
            }
        
        positive_count = 0
        negative_count = 0
        earnings_detected = False
        
        # Analyze each article
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
            
            # Check for earnings
            if any(keyword in text for keyword in self.EARNINGS_KEYWORDS):
                earnings_detected = True
            
            # Count positive/negative keywords
            pos_matches = sum(1 for keyword in self.POSITIVE_KEYWORDS if keyword in text)
            neg_matches = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text)
            
            if pos_matches > neg_matches:
                positive_count += 1
            elif neg_matches > pos_matches:
                negative_count += 1
        
        # Calculate polarity (-1 to +1)
        total_articles = len(articles)
        if total_articles == 0:
            polarity = 0.0
            confidence = 0.0
        else:
            # Polarity: (positive - negative) / total
            polarity = (positive_count - negative_count) / total_articles
            # Confidence: based on article count and agreement
            agreement = abs(positive_count - negative_count) / total_articles if total_articles > 0 else 0
            confidence = min(1.0, (total_articles / 10.0) * 0.5 + agreement * 0.5)
        
        # Generate summary
        if earnings_detected:
            summary = f"Earnings news detected. {positive_count} positive, {negative_count} negative articles"
        elif positive_count > negative_count:
            summary = f"Mostly positive news ({positive_count} positive, {negative_count} negative)"
        elif negative_count > positive_count:
            summary = f"Mostly negative news ({positive_count} positive, {negative_count} negative)"
        else:
            summary = f"Neutral news ({positive_count} positive, {negative_count} negative)"
        
        return {
            'polarity': float(polarity),
            'confidence': float(confidence),
            'summary': summary,
            'article_count': total_articles,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'earnings_detected': earnings_detected
        }
    
    def get_sentiment_for_symbol(self, symbol: str) -> Dict:
        """
        Get sentiment for a symbol (fetches news and calculates sentiment)
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Sentiment dict with polarity, confidence, summary
        """
        articles = self.get_stock_news(symbol, max_articles=10)
        sentiment = self.calculate_sentiment(articles)
        return sentiment
    
    def detect_earnings_event(self, symbol: str) -> bool:
        """
        Detect if there's an earnings event for the symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            True if earnings event detected
        """
        articles = self.get_stock_news(symbol, max_articles=5)
        sentiment = self.calculate_sentiment(articles)
        return sentiment.get('earnings_detected', False)
    
    def should_filter_out(self, symbol: str, negative_threshold: float = -0.3) -> bool:
        """
        Determine if stock should be filtered out due to negative news
        
        Args:
            symbol: Stock symbol
            negative_threshold: Polarity threshold below which to filter (default -0.3)
        
        Returns:
            True if should be filtered out
        """
        sentiment = self.get_sentiment_for_symbol(symbol)
        return sentiment['polarity'] < negative_threshold and sentiment['confidence'] > 0.5

