#!/usr/bin/env python3
"""
Build verification script - Tests core functionality without full market scan
"""

import sys
from config import Config
from database import PickLedger
from data_fetcher import MarketDataFetcher
from scanner_engine import ScannerEngine
from learning import LearningEngine
from output_formatter import OutputFormatter
from technical_indicators import TechnicalIndicators
from scoring_engine import ScoringEngine
from news_fetcher import NewsFetcher

def test_imports():
    """Test all imports"""
    print("✅ All imports successful")
    return True

def test_config():
    """Test config initialization"""
    config = Config()
    assert len(config.NIFTY_SYMBOLS) > 0, "Symbols should be loaded"
    assert config.MIN_CONVICTION_SCORE > 0, "Min conviction should be positive"
    print(f"✅ Config initialized: {len(config.NIFTY_SYMBOLS)} symbols, currency: {config.CURRENCY_SYMBOL}")
    return True

def test_database():
    """Test database initialization"""
    ledger = PickLedger()
    count = ledger.get_total_picks_count()
    print(f"✅ Database initialized: {count} picks in ledger")
    return True

def test_learning():
    """Test learning engine"""
    config = Config()
    ledger = PickLedger()
    learning = LearningEngine(config, ledger)
    mode = learning.get_learning_mode()
    print(f"✅ Learning engine initialized: mode={mode}")
    return True

def test_formatter():
    """Test output formatter"""
    formatter = OutputFormatter()
    # Test with empty picks
    output = formatter.format_picks([], "Jan 1, 2024")
    assert "No actionable" in output
    print("✅ Output formatter works")
    return True

def test_technical_indicators():
    """Test technical indicators"""
    import pandas as pd
    import numpy as np
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(50).cumsum() + 100,
        'high': np.random.randn(50).cumsum() + 102,
        'low': np.random.randn(50).cumsum() + 98,
        'close': np.random.randn(50).cumsum() + 100,
        'volume': np.random.randint(100000, 1000000, 50)
    })
    
    # Test indicators
    vwap = TechnicalIndicators.calculate_vwap(df)
    atr = TechnicalIndicators.calculate_atr(df)
    rsi = TechnicalIndicators.calculate_rsi(df)
    mas = TechnicalIndicators.calculate_moving_averages(df)
    
    assert vwap > 0, "VWAP should be positive"
    assert atr > 0, "ATR should be positive"
    assert 0 <= rsi <= 100, "RSI should be 0-100"
    assert 'ma_short' in mas, "MA should have short value"
    
    print("✅ Technical indicators work correctly")
    return True

def test_scoring_engine():
    """Test comprehensive scoring engine"""
    import pandas as pd
    import numpy as np
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(60).cumsum() + 100,
        'high': np.random.randn(60).cumsum() + 102,
        'low': np.random.randn(60).cumsum() + 98,
        'close': np.random.randn(60).cumsum() + 100,
        'volume': np.random.randint(100000, 1000000, 60)
    })
    
    entry_price = df['close'].iloc[-1]
    stop_loss = entry_price * 0.98
    target_price = entry_price * 1.05
    
    # Test all 7 dimensions
    trend = ScoringEngine.calculate_trend_score(df, entry_price)
    momentum = ScoringEngine.calculate_momentum_score(df, entry_price, 2.0)
    volume = ScoringEngine.calculate_volume_score(df, df['volume'].iloc[-1], True)
    volatility = ScoringEngine.calculate_volatility_score(df, 75.0)
    sentiment = ScoringEngine.calculate_sentiment_score({'polarity': 0.5, 'confidence': 0.8})
    liquidity = ScoringEngine.calculate_liquidity_score(df, 100000)
    risk = ScoringEngine.calculate_risk_score(df, entry_price, stop_loss, target_price, 75.0)
    
    # Validate scores are in range
    assert 0 <= trend <= 100, f"Trend score out of range: {trend}"
    assert 0 <= momentum <= 100, f"Momentum score out of range: {momentum}"
    assert 0 <= volume <= 100, f"Volume score out of range: {volume}"
    assert 0 <= volatility <= 100, f"Volatility score out of range: {volatility}"
    assert 0 <= sentiment <= 100, f"Sentiment score out of range: {sentiment}"
    assert 0 <= liquidity <= 100, f"Liquidity score out of range: {liquidity}"
    assert 0 <= risk <= 100, f"Risk score out of range: {risk}"
    
    # Test composite scoring
    scores = ScoringEngine.calculate_composite_scores(
        daily_df=df,
        intraday_df=None,
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_price=target_price,
        current_volume=df['volume'].iloc[-1],
        volume_surge=True,
        breakout_pct=2.0,
        volatility_percentile=75.0,
        sentiment_data={'polarity': 0.5, 'confidence': 0.8},
        min_avg_volume=100000
    )
    
    assert 'conviction_score' in scores, "Composite scores should include conviction_score"
    assert 'risk_score' in scores, "Composite scores should include risk_score"
    assert 'dimension_scores' in scores, "Composite scores should include dimension_scores"
    assert 0 <= scores['conviction_score'] <= 100, "Conviction score out of range"
    assert len(scores['dimension_scores']) == 7, "Should have 7 dimension scores"
    
    print("✅ Scoring engine works correctly (all 7 dimensions)")
    return True

def test_news_fetcher():
    """Test news fetcher (basic functionality)"""
    fetcher = NewsFetcher(cache_duration_minutes=1)
    
    # Test sentiment calculation with mock data
    mock_articles = [
        {'title': 'Stock profit growth surge', 'summary': 'Company beats earnings'},
        {'title': 'Stock decline loss', 'summary': 'Company misses guidance'}
    ]
    
    sentiment = fetcher.calculate_sentiment(mock_articles)
    
    assert 'polarity' in sentiment, "Sentiment should have polarity"
    assert 'confidence' in sentiment, "Sentiment should have confidence"
    assert -1 <= sentiment['polarity'] <= 1, "Polarity should be -1 to 1"
    assert 0 <= sentiment['confidence'] <= 1, "Confidence should be 0 to 1"
    
    # Test earnings detection
    earnings_articles = [
        {'title': 'Company earnings results Q1', 'summary': 'Quarterly financial results'}
    ]
    earnings_sentiment = fetcher.calculate_sentiment(earnings_articles)
    assert earnings_sentiment.get('earnings_detected', False) == True, "Should detect earnings"
    
    print("✅ News fetcher works correctly")
    return True

def test_strategies_with_scoring():
    """Test strategies use new scoring system"""
    import pandas as pd
    import numpy as np
    from strategies.momentum_strategy import MomentumSwing
    
    config = Config()
    strategy = MomentumSwing(config)
    
    # Create sample daily data
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    daily_df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(60).cumsum() + 100,
        'high': np.random.randn(60).cumsum() + 102,
        'low': np.random.randn(60).cumsum() + 98,
        'close': np.random.randn(60).cumsum() + 100,
        'volume': np.random.randint(200000, 2000000, 60)
    })
    
    # Test strategy analysis
    result = strategy.analyze('TEST.NS', daily_df, {'polarity': 0.3, 'confidence': 0.7})
    
    # If result exists, check it has dimension_scores
    if result:
        assert 'dimension_scores' in result, "Strategy result should include dimension_scores"
        assert 'conviction_score' in result, "Strategy result should include conviction_score"
        assert len(result['dimension_scores']) == 7, "Should have 7 dimension scores"
    
    print("✅ Strategies integrate with scoring engine")
    return True

def test_scanner_with_news():
    """Test scanner engine initializes with news fetcher"""
    config = Config()
    scanner = ScannerEngine(config)
    
    # Check news fetcher is initialized
    assert hasattr(scanner, 'news_fetcher'), "Scanner should have news_fetcher"
    assert scanner.news_fetcher is not None, "News fetcher should be initialized"
    
    print("✅ Scanner engine integrates with news fetcher")
    return True

def main():
    """Run all tests"""
    print("🔍 Running build verification tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Config", test_config),
        ("Database", test_database),
        ("Learning", test_learning),
        ("Formatter", test_formatter),
        ("Technical Indicators", test_technical_indicators),
        ("Scoring Engine", test_scoring_engine),
        ("News Fetcher", test_news_fetcher),
        ("Strategies with Scoring", test_strategies_with_scoring),
        ("Scanner with News", test_scanner_with_news),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(tests)}")
        sys.exit(1)
    else:
        print("✅ All build tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())

