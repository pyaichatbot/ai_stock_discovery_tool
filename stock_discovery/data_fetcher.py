"""
AI-Powered Stock Discovery Tool - Market Data Fetcher
"""

import yfinance as yf
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta


class MarketDataFetcher:
    """Fetch real-time and historical market data"""
    
    @staticmethod
    def get_stock_data(symbol: str, period: str = "5d", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            # Reset index and normalize column names
            df = df.reset_index()
            
            # Handle both 'Date' and 'Datetime' columns
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'datetime'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'datetime'})
            
            # Normalize all column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            return df
        
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    @staticmethod
    def get_intraday_data(symbol: str) -> Optional[pd.DataFrame]:
        """Fetch 1-minute intraday data (last 5 days max from yfinance)"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval="1m")
            
            if df.empty:
                return None
            
            # Reset index and normalize column names
            df = df.reset_index()
            
            # Handle both 'Date' and 'Datetime' columns
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'datetime'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'datetime'})
            
            # Normalize all column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Ensure datetime is timezone-naive for easier comparison
            if 'datetime' in df.columns and pd.api.types.is_datetime64_any_dtype(df['datetime']):
                df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize(None)
            
            return df
        
        except Exception as e:
            return None
    
    @staticmethod
    def get_current_price(symbol: str) -> Optional[float]:
        """Get latest price"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            # Fallback to daily data
            data = ticker.history(period="1d", interval="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            return None
        except:
            return None
    
    @staticmethod
    def get_index_trend(index_symbol: str = "^NSEI") -> str:
        """Determine NIFTY trend (bullish/bearish/neutral)"""
        try:
            df = MarketDataFetcher.get_stock_data(index_symbol, period="20d", interval="1d")
            if df is None or len(df) < 20:
                return "neutral"
            
            close = df['close'].values
            ma_20 = close[-20:].mean()
            current = close[-1]
            
            if current > ma_20 * 1.01:
                return "bullish"
            elif current < ma_20 * 0.99:
                return "bearish"
            return "neutral"
        except:
            return "neutral"
    
    @staticmethod
    def compute_outcome(symbol: str, entry_price: float, stop_loss: float, 
                       target_price: float, entry_timestamp: str, 
                       horizon_days: int = 1) -> dict:
        """
        Compute outcome for a pick after holding period
        Returns MFE, MAE, final_return, hit_target, hit_stop
        """
        try:
            # Parse entry timestamp
            entry_dt = pd.to_datetime(entry_timestamp)
            
            # Fetch data from entry to now
            end_dt = datetime.now()
            days_diff = (end_dt - entry_dt).days + 5  # Add buffer
            
            df = MarketDataFetcher.get_stock_data(
                symbol, 
                period=f"{max(days_diff, 5)}d", 
                interval="1d"
            )
            
            if df is None or df.empty:
                return {
                    'mfe': 0.0,
                    'mae': 0.0,
                    'final_return': 0.0,
                    'hit_target': False,
                    'hit_stop': False
                }
            
            # Filter to data after entry
            df['datetime'] = pd.to_datetime(df['datetime'])
            mask = df['datetime'] >= entry_dt
            df = df[mask]
            
            if df.empty:
                return {
                    'mfe': 0.0,
                    'mae': 0.0,
                    'final_return': 0.0,
                    'hit_target': False,
                    'hit_stop': False
                }
            
            # Limit to horizon
            df = df.head(horizon_days)
            
            # Calculate MFE and MAE
            highs = df['high'].values
            lows = df['low'].values
            
            mfe = ((highs.max() - entry_price) / entry_price) * 100
            mae = ((lows.min() - entry_price) / entry_price) * 100
            
            # Check if target or stop was hit
            hit_target = highs.max() >= target_price
            hit_stop = lows.min() <= stop_loss
            
            # Final return at end of horizon
            final_price = df['close'].iloc[-1]
            final_return = ((final_price - entry_price) / entry_price) * 100
            
            return {
                'mfe': float(mfe),
                'mae': float(mae),
                'final_return': float(final_return),
                'hit_target': hit_target,
                'hit_stop': hit_stop
            }
        
        except Exception as e:
            print(f"Error computing outcome for {symbol}: {e}")
            return {
                'mfe': 0.0,
                'mae': 0.0,
                'final_return': 0.0,
                'hit_target': False,
                'hit_stop': False
            }
