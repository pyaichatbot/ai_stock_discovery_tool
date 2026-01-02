"""
Symbol Loader - Dynamic NSE symbol fetching
Supports: Yahoo Finance, NSE India website, manual CSV
"""

import yfinance as yf
import pandas as pd
import json
from typing import List, Optional
from datetime import datetime, timedelta
import pickle
import os
import requests
import time


class SymbolLoader:
    """Load NSE symbols dynamically from various sources"""
    
    CACHE_FILE = "symbols_cache.pkl"
    CACHE_DURATION_DAYS = 7  # Refresh weekly
    
    def __init__(self, cache_dir: str = "."):
        self.cache_dir = cache_dir
        self.cache_path = os.path.join(cache_dir, self.CACHE_FILE)
    
    def get_symbols(self, source: str = "nifty50", refresh: bool = False) -> List[str]:
        """
        Get NSE symbols from specified source
        
        Args:
            source: 'nifty50', 'nifty100', 'nifty200', 'nifty500', 'csv'
            refresh: Force refresh cache
            
        Returns:
            List of symbols with .NS suffix for Yahoo Finance
        """
        # Check cache first
        if not refresh:
            cached = self._load_from_cache(source)
            if cached:
                print(f"📦 Loaded {len(cached)} symbols from cache")
                return cached
        
        # Fetch fresh symbols
        print(f"🔄 Fetching symbols from {source}...")
        
        if source == "csv":
            symbols = self._load_from_csv()
        elif source.startswith("nifty"):
            # Try NSE API first, then fallback to hardcoded
            symbols = self._load_nifty_index(source)
        else:
            raise ValueError(f"Unknown source: {source}")
        
        if symbols:
            self._save_to_cache(source, symbols)
            print(f"✅ Loaded {len(symbols)} symbols")
        
        return symbols
    
    def _fetch_from_nse_api(self, index_name: str) -> Optional[List[str]]:
        """
        Fetch symbols from NSE India official API
        
        Args:
            index_name: 'nifty50', 'nifty100', 'nifty200', etc.
        
        Returns:
            List of symbols with .NS suffix, or None if API fails
        """
        # Map index names to NSE API format
        index_map = {
            'nifty50': 'NIFTY 50',
            'nifty100': 'NIFTY 100',
            'nifty200': 'NIFTY 200',
            'nifty500': 'NIFTY 500'
        }
        
        nse_index_name = index_map.get(index_name, 'NIFTY 50')
        
        try:
            # NSE API endpoint
            url = f"https://www.nseindia.com/api/equity-stockIndices?index={nse_index_name.replace(' ', '%20')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.nseindia.com/'
            }
            
            # Create session for cookie handling
            session = requests.Session()
            session.headers.update(headers)
            
            # First request to get cookies (NSE sometimes requires this)
            session.get('https://www.nseindia.com', timeout=10)
            time.sleep(0.5)  # Small delay to avoid rate limiting
            
            # Fetch index data
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  NSE API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            if 'data' not in data or not isinstance(data['data'], list):
                print(f"⚠️  NSE API response format unexpected")
                return None
            
            # Extract symbols (skip index itself if present)
            symbols = []
            for item in data['data']:
                symbol = item.get('symbol', '')
                # Skip the index itself (e.g., 'NIFTY 50')
                if symbol and symbol != nse_index_name and 'NIFTY' not in symbol.upper():
                    symbols.append(symbol)
            
            if not symbols:
                print(f"⚠️  No symbols found in NSE API response")
                return None
            
            # Add .NS suffix for Yahoo Finance compatibility
            symbols_with_suffix = [f"{s}.NS" for s in symbols]
            
            print(f"✅ Fetched {len(symbols_with_suffix)} symbols from NSE API for {nse_index_name}")
            return symbols_with_suffix
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  NSE API request failed: {e}")
            return None
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  NSE API response parsing failed: {e}")
            return None
        except Exception as e:
            print(f"⚠️  NSE API error: {e}")
            return None
    
    def _load_nifty_index(self, index_name: str) -> List[str]:
        """
        Load symbols from NIFTY indices
        Tries NSE API first, falls back to hardcoded lists
        """
        # Try NSE API first
        api_symbols = self._fetch_from_nse_api(index_name)
        if api_symbols:
            return api_symbols
        
        # Fallback to hardcoded lists
        print(f"⚠️  NSE API failed, using hardcoded list for {index_name}")
        
        # NIFTY 50 symbols (most liquid)
        nifty50 = [
            "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
            "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL",
            "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
            "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
            "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
            "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT",
            "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC",
            "POWERGRID", "RELIANCE", "SBILIFE", "SHREECEM", "SBIN",
            "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
            "TECHM", "TITAN", "ULTRACEMCO", "UPL", "WIPRO"
        ]
        
        # NIFTY Next 50 (for NIFTY 100)
        nifty_next50 = [
            "ADANIGREEN", "ADANIPOWER", "AMBUJACEM", "ATGL", "BAJAJHLDNG",
            "BANDHANBNK", "BANKBARODA", "BERGEPAINT", "BEL", "BOSCHLTD",
            "CANBK", "CHOLAFIN", "COLPAL", "DABUR", "DLF",
            "DMART", "GAIL", "GODREJCP", "HAVELLS", "HDFCAMC",
            "HINDZINC", "ICICIPRULI", "IDEA", "INDHOTEL", "INDIGO",
            "IOC", "IRCTC", "IGL", "JINDALSTEL", "JIOFIN",
            "LICHSGFIN", "LTIM", "MARICO", "MCDOWELL-N", "NYKAA",
            "PAGEIND", "PIDILITIND", "PEL", "PERSISTENT", "PFC",
            "PGHH", "PIDILITIND", "PNB", "RECLTD", "SBICARD",
            "SHRIRAMFIN", "SIEMENS", "SRF", "TATAPOWER", "VEDL"
        ]
        
        if index_name == "nifty50":
            symbols = nifty50
        elif index_name == "nifty100":
            symbols = nifty50 + nifty_next50
        elif index_name == "nifty200":
            # For NIFTY 200, we'll use a curated list of top 200 stocks
            symbols = nifty50 + nifty_next50 + self._get_additional_nifty200()
        elif index_name == "nifty500":
            # For NIFTY 500, recommend using CSV or smaller universe
            print("⚠️  NIFTY 500 is large. Consider using NIFTY 200 or CSV file.")
            symbols = nifty50 + nifty_next50 + self._get_additional_nifty200()
        else:
            symbols = nifty50
        
        # Add .NS suffix for Yahoo Finance
        return [f"{symbol}.NS" for symbol in symbols]
    
    def _get_additional_nifty200(self) -> List[str]:
        """Additional stocks for NIFTY 200"""
        return [
            "ACC", "ABFRL", "APOLLOTYRE", "ASHOKLEY", "AUROPHARMA",
            "BALRAMCHIN", "BATAINDIA", "BHEL", "BIOCON", "BOSCHLTD",
            "BRITANNIA", "CUMMINSIND", "ESCORTS", "EXIDEIND", "FEDERALBNK",
            "GLENMARK", "GUJGASLTD", "HAVELLS", "HDFCAMC", "HINDCOPPER",
            "HINDPETRO", "IBULHSGFIN", "IDFCFIRSTB", "INDIACEM", "INDUSTOWER",
            "JUBLFOOD", "LTI", "LUPIN", "MRF", "MUTHOOTFIN",
            "NATIONALUM", "NMDC", "OBEROIRLTY", "OFSS", "OIL",
            "PAGEIND", "PETRONET", "PIIND", "PVR", "RAMCOCEM",
            "SAIL", "SBICARD", "SRTRANSFIN", "TORNTPHARM", "TRENT",
            "TVSMOTOR", "UBL", "MCDOWELL-N", "ZEEL", "ZYDUSLIFE",
            # Add more as needed
        ]
    
    def _load_from_csv(self, csv_path: str = "symbols.csv") -> List[str]:
        """
        Load symbols from CSV file
        
        CSV format:
        symbol
        RELIANCE
        TCS
        INFY
        
        Or with .NS:
        symbol
        RELIANCE.NS
        TCS.NS
        """
        try:
            df = pd.read_csv(csv_path)
            
            if 'symbol' not in df.columns:
                print("❌ CSV must have 'symbol' column")
                return []
            
            symbols = df['symbol'].tolist()
            
            # Add .NS suffix if not present
            symbols = [s if s.endswith('.NS') else f"{s}.NS" for s in symbols]
            
            return symbols
        
        except FileNotFoundError:
            print(f"❌ CSV file not found: {csv_path}")
            print("   Create a CSV with 'symbol' column containing NSE stock symbols")
            return []
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def _load_from_cache(self, source: str) -> Optional[List[str]]:
        """Load symbols from cache if not expired"""
        if not os.path.exists(self.cache_path):
            return None
        
        try:
            with open(self.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            if source not in cache_data:
                return None
            
            cached_time, symbols = cache_data[source]
            
            # Check if cache is expired
            if datetime.now() - cached_time > timedelta(days=self.CACHE_DURATION_DAYS):
                print("⏰ Cache expired, will refresh")
                return None
            
            return symbols
        
        except Exception as e:
            print(f"⚠️  Cache load error: {e}")
            return None
    
    def _save_to_cache(self, source: str, symbols: List[str]):
        """Save symbols to cache"""
        try:
            # Load existing cache
            cache_data = {}
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
            
            # Update with new data
            cache_data[source] = (datetime.now(), symbols)
            
            # Save
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 Cached {len(symbols)} symbols")
        
        except Exception as e:
            print(f"⚠️  Cache save error: {e}")
    
    def validate_symbols(self, symbols: List[str], sample_size: int = 10) -> List[str]:
        """
        Validate that symbols are tradeable on Yahoo Finance
        Tests a sample to avoid rate limits
        
        Args:
            symbols: List of symbols to validate
            sample_size: Number of symbols to test
            
        Returns:
            List of valid symbols
        """
        if not symbols:
            return []
        
        print(f"🔍 Validating symbols (testing {min(sample_size, len(symbols))} samples)...")
        
        # Test a sample
        import random
        test_symbols = random.sample(symbols, min(sample_size, len(symbols)))
        
        valid_count = 0
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period="1d")
                if not info.empty:
                    valid_count += 1
            except:
                pass
        
        success_rate = valid_count / len(test_symbols)
        
        if success_rate < 0.5:
            print(f"⚠️  Low validation rate: {success_rate*100:.0f}%")
            print("   Some symbols may not be available on Yahoo Finance")
        else:
            print(f"✅ Validation rate: {success_rate*100:.0f}%")
        
        return symbols
    
    def create_custom_list(self, symbols: List[str], output_file: str = "custom_symbols.csv"):
        """
        Create a custom CSV file from a list of symbols
        
        Args:
            symbols: List of symbols (with or without .NS)
            output_file: Output CSV filename
        """
        # Ensure .NS suffix
        symbols = [s if s.endswith('.NS') else f"{s}.NS" for s in symbols]
        
        df = pd.DataFrame({'symbol': symbols})
        df.to_csv(output_file, index=False)
        
        print(f"✅ Created {output_file} with {len(symbols)} symbols")
        print(f"   Use: config.load_symbols('csv', csv_path='{output_file}')")


def get_zerodha_popular_stocks() -> List[str]:
    """
    Get list of popular stocks commonly traded on Zerodha
    These are high-liquidity stocks suitable for intraday/swing trading
    """
    popular = [
        # Large Cap - High Liquidity
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
        "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
        
        # Mid Cap - Good Liquidity  
        "ADANIPORTS", "AXISBANK", "BAJFINANCE", "BAJAJFINSV", "ASIANPAINT",
        "MARUTI", "LT", "SUNPHARMA", "TITAN", "ULTRACEMCO",
        
        # Popular Trading Stocks
        "TATAMOTORS", "TATASTEEL", "JSWSTEEL", "HINDALCO", "NTPC",
        "POWERGRID", "ONGC", "COALINDIA", "BPCL", "IOC",
        
        # Tech Stocks
        "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT",
        
        # Pharma
        "DRREDDY", "CIPLA", "DIVISLAB", "AUROPHARMA", "LUPIN",
        
        # Auto
        "M&M", "EICHERMOT", "HEROMOTOCO", "BAJAJ-AUTO", "TVSMOTOR",
        
        # Banks/Finance
        "INDUSINDBK", "BANKBARODA", "PNB", "SBILIFE", "HDFCLIFE",
        "BAJAJHLDNG", "CHOLAFIN", "SHRIRAMFIN",
        
        # Others
        "NESTLEIND", "BRITANNIA", "DABUR", "MARICO", "GODREJCP",
        "DLF", "GRASIM", "AMBUJACEM", "DMART", "TRENT"
    ]
    
    return [f"{s}.NS" for s in popular]


# Convenience functions for config.py

def load_nifty50() -> List[str]:
    """Quick loader for NIFTY 50"""
    loader = SymbolLoader()
    return loader.get_symbols("nifty50")


def load_nifty100() -> List[str]:
    """Quick loader for NIFTY 100"""
    loader = SymbolLoader()
    return loader.get_symbols("nifty100")


def load_nifty200() -> List[str]:
    """Quick loader for NIFTY 200"""
    loader = SymbolLoader()
    return loader.get_symbols("nifty200")


def load_zerodha_popular() -> List[str]:
    """Quick loader for Zerodha popular stocks"""
    return get_zerodha_popular_stocks()


def load_from_csv(csv_path: str = "symbols.csv") -> List[str]:
    """Quick loader from CSV"""
    loader = SymbolLoader()
    return loader._load_from_csv(csv_path)
