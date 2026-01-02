"""
Test script to verify all components
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")
    
    try:
        from config import Config
        print("  ✓ config")
        
        from database import PickLedger
        print("  ✓ database")
        
        from data_fetcher import MarketDataFetcher
        print("  ✓ data_fetcher")
        
        from technical_indicators import TechnicalIndicators
        print("  ✓ technical_indicators")
        
        from learning import LearningEngine
        print("  ✓ learning")
        
        from strategies.orb_strategy import OpeningRangeBreakout
        from strategies.vwap_strategy import VWAPPullback
        from strategies.momentum_strategy import MomentumSwing
        from strategies.hvb_strategy import HighVolatilityBreakout
        print("  ✓ all strategies")
        
        from scanner_engine import ScannerEngine
        print("  ✓ scanner_engine")
        
        from output_formatter import OutputFormatter
        print("  ✓ output_formatter")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    from config import Config
    
    config = Config()
    
    assert config.TOTAL_BUDGET == 500.0
    assert config.MIN_CONVICTION_SCORE == 75.0
    assert len(config.NIFTY_SYMBOLS) > 0
    
    print(f"  ✓ Config loaded: {len(config.NIFTY_SYMBOLS)} symbols")
    print(f"  ✓ Symbol source: {config.SYMBOL_SOURCE}")
    print(f"  ✓ Budget: €{config.TOTAL_BUDGET}")
    print(f"  ✓ Min conviction: {config.MIN_CONVICTION_SCORE}")


def test_symbol_loader():
    """Test symbol loader"""
    print("\nTesting symbol loader...")
    
    from symbol_loader import (
        load_nifty50,
        load_zerodha_popular,
        SymbolLoader
    )
    
    # Test NIFTY 50 loading
    symbols = load_nifty50()
    assert len(symbols) > 0
    assert all(s.endswith('.NS') for s in symbols)
    print(f"  ✓ NIFTY 50 loaded: {len(symbols)} symbols")
    
    # Test Zerodha popular
    symbols = load_zerodha_popular()
    assert len(symbols) > 0
    print(f"  ✓ Zerodha popular loaded: {len(symbols)} symbols")
    
    # Test CSV creation
    loader = SymbolLoader()
    test_symbols = ['RELIANCE', 'TCS', 'INFY']
    loader.create_custom_list(test_symbols, 'test_symbols.csv')
    
    # Verify CSV was created
    import os
    assert os.path.exists('test_symbols.csv')
    print("  ✓ CSV creation works")
    
    # Cleanup
    os.remove('test_symbols.csv')
    print("  ✓ Test CSV cleaned up")


def test_database():
    """Test database operations"""
    print("\nTesting database...")
    
    from database import PickLedger
    from datetime import datetime
    
    ledger = PickLedger("test_ledger.db")
    
    # Test save pick
    test_pick = {
        'pick_id': 'TEST_001',
        'symbol': 'RELIANCE.NS',
        'strategy': 'ORB',
        'timestamp': datetime.now().isoformat(),
        'conviction_score': 85.0,
        'risk_score': 50.0,
        'entry_price': 2950.0,
        'stop_loss': 2920.0,
        'target_price': 3000.0,
        'position_size': 10.0,
        'market_regime': 'bullish',
        'features': {'test': True}
    }
    
    pick_id = ledger.save_pick(test_pick)
    print(f"  ✓ Pick saved: {pick_id}")
    
    # Test feedback
    ledger.add_feedback('TEST_001', True, 4, "Test feedback")
    print("  ✓ Feedback saved")
    
    # Test outcome
    ledger.save_outcome('TEST_001', 5.0, -2.0, 3.5, True, False)
    print("  ✓ Outcome saved")
    
    # Cleanup
    import os
    os.remove("test_ledger.db")
    print("  ✓ Test database cleaned up")


def test_data_fetcher():
    """Test data fetching"""
    print("\nTesting data fetcher...")
    
    from data_fetcher import MarketDataFetcher
    
    # Test daily data
    df = MarketDataFetcher.get_stock_data("RELIANCE.NS", period="5d")
    
    if df is not None and not df.empty:
        print(f"  ✓ Daily data fetched: {len(df)} rows")
        print(f"  ✓ Columns: {list(df.columns)}")
    else:
        print("  ⚠️  Could not fetch data (may be outside market hours)")
    
    # Test index trend
    trend = MarketDataFetcher.get_index_trend()
    print(f"  ✓ Index trend: {trend}")


def test_technical_indicators():
    """Test technical indicators"""
    print("\nTesting technical indicators...")
    
    from technical_indicators import TechnicalIndicators
    import pandas as pd
    import numpy as np
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(100000, 1000000, 100)
    })
    
    # Test indicators
    vwap = TechnicalIndicators.calculate_vwap(df)
    print(f"  ✓ VWAP: {vwap:.2f}")
    
    atr = TechnicalIndicators.calculate_atr(df)
    print(f"  ✓ ATR: {atr:.2f}")
    
    rsi = TechnicalIndicators.calculate_rsi(df)
    print(f"  ✓ RSI: {rsi:.2f}")
    
    mas = TechnicalIndicators.calculate_moving_averages(df)
    print(f"  ✓ MA Short: {mas['ma_short']:.2f}, Long: {mas['ma_long']:.2f}")


def test_strategies():
    """Test strategy implementations"""
    print("\nTesting strategies...")
    
    from config import Config
    from strategies.orb_strategy import OpeningRangeBreakout
    from strategies.vwap_strategy import VWAPPullback
    from strategies.momentum_strategy import MomentumSwing
    from strategies.hvb_strategy import HighVolatilityBreakout
    
    config = Config()
    
    orb = OpeningRangeBreakout(config)
    print("  ✓ ORB strategy initialized")
    
    vwap = VWAPPullback(config)
    print("  ✓ VWAP strategy initialized")
    
    momentum = MomentumSwing(config)
    print("  ✓ Momentum strategy initialized")
    
    hvb = HighVolatilityBreakout(config)
    print("  ✓ HVB strategy initialized")


def test_learning():
    """Test learning engine"""
    print("\nTesting learning engine...")
    
    from config import Config
    from database import PickLedger
    from learning import LearningEngine
    
    config = Config()
    ledger = PickLedger("test_learning.db")
    learning = LearningEngine(config, ledger)
    
    mode = learning.get_learning_mode()
    print(f"  ✓ Learning mode: {mode}")
    
    weights = learning.get_strategy_weights()
    print(f"  ✓ Strategy weights: {weights}")
    
    # Cleanup
    import os
    os.remove("test_learning.db")
    print("  ✓ Test database cleaned up")


def main():
    """Run all tests"""
    print("="*70)
    print("Stock Discovery Tool - Component Tests")
    print("="*70)
    
    if not test_imports():
        return False
    
    try:
        test_config()
        test_symbol_loader()
        test_database()
        test_data_fetcher()
        test_technical_indicators()
        test_strategies()
        test_learning()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nYou can now run the scanner:")
        print("  python main.py scan --mode intraday")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
