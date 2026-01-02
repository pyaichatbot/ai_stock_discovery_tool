"""
AI-Powered Stock Discovery Tool - Configuration
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Config:
    """Central configuration management"""
    
    # Trading Parameters
    TOTAL_BUDGET: float = 500.0  # Trading capital
    CURRENCY_SYMBOL: str = "₹"  # Currency symbol for display (₹ for INR, $ for USD, € for EUR)
    MAX_RISK_PER_TRADE: float = 0.02  # 2%
    MIN_CONVICTION_SCORE: float = 60.0  # Lowered to find more opportunities
    TOP_N_PICKS: int = 3
    
    # Market Parameters
    MIN_AVG_VOLUME: int = 100000
    MIN_PRICE: float = 50.0
    MAX_PRICE: float = 5000.0
    
    # Strategy Parameters
    ORB_PERIOD_MINUTES: int = 15
    VWAP_LOOKBACK_DAYS: int = 20
    MOMENTUM_MA_SHORT: int = 20
    MOMENTUM_MA_LONG: int = 50
    
    # HVB Mode
    HVB_ENABLED: bool = False
    HVB_MAX_PICKS: int = 1
    HVB_MIN_VOLATILITY_PERCENTILE: float = 90.0
    
    # Penny Stock Mode (High Risk - Opt-in only)
    PENNY_STOCK_MODE_ENABLED: bool = False
    PENNY_STOCK_MIN_PRICE: float = 1.0  # Stocks below ₹50
    PENNY_STOCK_MAX_PRICE: float = 50.0
    PENNY_STOCK_MAX_PICKS: int = 2  # Limit exposure to penny stocks
    PENNY_STOCK_MAX_RISK_PCT: float = 0.01  # 1% risk per trade (stricter than normal)
    
    # Risk Management
    MAX_DAILY_LOSS_PCT: float = 0.05  # 5% of total budget
    MAX_CONCURRENT_POSITIONS: int = 5
    MAX_VOLATILITY_PERCENTILE: float = 95.0  # No trade if volatility > 95th percentile
    
    # Automation/Scheduling
    AUTOMATION_ENABLED: bool = False
    PRE_MARKET_SCAN_TIME: str = "09:00"  # IST
    INTRADAY_REFRESH_INTERVAL: int = 30  # minutes
    EOD_SUMMARY_TIME: str = "15:30"  # IST
    WEEKLY_REVIEW_DAY: str = "sunday"
    
    # Learning Parameters
    MIN_TRADES_BEFORE_LEARNING: int = 10
    CONSERVATIVE_LEARNING_THRESHOLD: int = 50
    WEIGHT_ADJUSTMENT_CONSERVATIVE: float = 0.05  # ±5%
    WEIGHT_ADJUSTMENT_FULL: float = 0.20  # ±20%
    
    # Symbol Loading Configuration
    # Options: 'nifty50', 'nifty100', 'nifty200', 'nifty500', 
    #          'nifty_smallcap100', 'nifty_smallcap250', 'nifty_midcap150',
    #          'zerodha_popular', 'csv', 'manual', 'penny_stocks'
    SYMBOL_SOURCE: str = 'nifty50'
    SYMBOL_CSV_PATH: str = 'symbols.csv'  # Used if SYMBOL_SOURCE = 'csv'
    REFRESH_SYMBOLS: bool = False  # Set True to force refresh from source
    
    # Stock Universe (loaded dynamically)
    NIFTY_SYMBOLS: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Load symbols dynamically based on SYMBOL_SOURCE"""
        if not self.NIFTY_SYMBOLS:  # Only load if not already set
            self.NIFTY_SYMBOLS = self._load_symbols()
    
    def _load_symbols(self) -> List[str]:
        """Load symbols based on configured source"""
        from symbol_loader import (
            SymbolLoader, 
            load_nifty50, 
            load_nifty100, 
            load_nifty200,
            load_nifty_smallcap100,
            load_nifty_smallcap250,
            load_penny_stocks_from_price_filter,
            load_zerodha_popular,
            load_from_csv
        )
        
        print(f"📊 Loading symbols from: {self.SYMBOL_SOURCE}")
        
        
        try:
            if self.SYMBOL_SOURCE == 'nifty50':
                symbols = load_nifty50()
            elif self.SYMBOL_SOURCE == 'nifty100':
                symbols = load_nifty100()
            elif self.SYMBOL_SOURCE == 'nifty200':
                symbols = load_nifty200()
            elif self.SYMBOL_SOURCE == 'nifty_smallcap100':
                symbols = load_nifty_smallcap100()
            elif self.SYMBOL_SOURCE == 'nifty_smallcap250':
                symbols = load_nifty_smallcap250()
            elif self.SYMBOL_SOURCE == 'penny_stocks':
                # Filter penny stocks by price from smallcap index
                symbols = load_penny_stocks_from_price_filter(
                    max_price=self.PENNY_STOCK_MAX_PRICE,
                    source='nifty_smallcap250'
                )
            elif self.SYMBOL_SOURCE == 'zerodha_popular':
                symbols = load_zerodha_popular()
            elif self.SYMBOL_SOURCE == 'csv':
                symbols = load_from_csv(self.SYMBOL_CSV_PATH)
            elif self.SYMBOL_SOURCE == 'manual':
                # Use hardcoded fallback
                symbols = self._get_fallback_symbols()
            else:
                print(f"⚠️  Unknown source '{self.SYMBOL_SOURCE}', using NIFTY 50")
                symbols = load_nifty50()
            
            if not symbols:
                print("⚠️  No symbols loaded, using fallback")
                symbols = self._get_fallback_symbols()
            
            return symbols
        
        except Exception as e:
            print(f"❌ Error loading symbols: {e}")
            print("   Using fallback NIFTY 50 symbols")
            return self._get_fallback_symbols()
    
    def _get_fallback_symbols(self) -> List[str]:
        """Fallback hardcoded symbols (NIFTY 50)"""
        return [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
            "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LT.NS", "ITC.NS",
            "KOTAKBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS",
            "MARUTI.NS", "HCLTECH.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
            "NESTLEIND.NS", "WIPRO.NS", "TATAMOTORS.NS", "ONGC.NS", "NTPC.NS",
            "ADANIPORTS.NS", "POWERGRID.NS", "M&M.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
            "TECHM.NS", "INDUSINDBK.NS", "BAJAJFINSV.NS", "HINDALCO.NS", "COALINDIA.NS",
            "DRREDDY.NS", "EICHERMOT.NS", "BRITANNIA.NS", "GRASIM.NS", "DIVISLAB.NS",
            "TATACONSUM.NS", "CIPLA.NS", "BPCL.NS", "HEROMOTOCO.NS", "SHREECEM.NS",
            "SBILIFE.NS", "APOLLOHOSP.NS", "UPL.NS", "ADANIENT.NS", "LTIM.NS", "HDFCLIFE.NS"
        ]
