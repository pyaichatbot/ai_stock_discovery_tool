"""
Backtesting Engine - Test strategies on historical data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .config import Config
from .data_fetcher import MarketDataFetcher
from .scanner_engine import ScannerEngine
from .strategies.orb_strategy import OpeningRangeBreakout
from .strategies.vwap_strategy import VWAPPullback
from .strategies.momentum_strategy import MomentumSwing
from .strategies.hvb_strategy import HighVolatilityBreakout
from .strategies.earnings_strategy import EarningsEventDrift


@dataclass
class BacktestResult:
    """Results from a single backtest"""
    strategy: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    best_trade: float
    worst_trade: float


@dataclass
class Trade:
    """Represents a single trade"""
    symbol: str
    strategy: str
    entry_date: datetime
    entry_price: float
    stop_loss: float
    target_price: float
    exit_date: Optional[datetime]
    exit_price: Optional[float]
    return_pct: Optional[float]
    status: str  # 'open', 'win', 'loss', 'breakeven'


class BacktestingEngine:
    """Backtest strategies on historical data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.fetcher = MarketDataFetcher()
        
        # Initialize strategies
        self.orb = OpeningRangeBreakout(config)
        self.vwap = VWAPPullback(config)
        self.momentum = MomentumSwing(config)
        self.hvb = HighVolatilityBreakout(config)
        self.earnings = EarningsEventDrift(config)
    
    def backtest_strategy(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        mode: str = "swing"
    ) -> BacktestResult:
        """
        Backtest a single strategy
        
        Args:
            strategy_name: 'ORB', 'VWAP_PULLBACK', 'MOMENTUM_SWING', 'HVB', 'EARNINGS_DRIFT'
            symbols: List of symbols to test
            start_date: Start of backtest period
            end_date: End of backtest period
            mode: 'intraday' or 'swing'
        
        Returns:
            BacktestResult with performance metrics
        """
        trades = []
        equity_curve = []
        current_equity = 100000  # Starting capital
        
        # Get date range
        current_date = start_date
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        print(f"🔄 Backtesting {strategy_name} on {len(symbols)} symbols...")
        print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Simulate trading day by day
        for date in date_range:
            if date.weekday() >= 5:  # Skip weekends
                continue
            
            # Check for exit conditions on open trades
            for trade in trades:
                if trade.status == 'open':
                    exit_result = self._check_exit(trade, date)
                    if exit_result:
                        trade.exit_date = exit_result['exit_date']
                        trade.exit_price = exit_result['exit_price']
                        trade.return_pct = exit_result['return_pct']
                        trade.status = exit_result['status']
                        
                        # Update equity
                        if trade.return_pct:
                            current_equity *= (1 + trade.return_pct / 100)
                        equity_curve.append({
                            'date': date,
                            'equity': current_equity,
                            'return_pct': trade.return_pct or 0
                        })
            
            # Look for new entry signals
            for symbol in symbols:
                # Check if we already have an open position in this symbol
                if any(t.symbol == symbol and t.status == 'open' for t in trades):
                    continue
                
                # Get historical data up to this date
                signal = self._get_historical_signal(symbol, strategy_name, date, mode)
                
                if signal:
                    # Create trade
                    trade = Trade(
                        symbol=symbol,
                        strategy=strategy_name,
                        entry_date=date,
                        entry_price=signal['entry_price'],
                        stop_loss=signal['stop_loss'],
                        target_price=signal['target_price'],
                        exit_date=None,
                        exit_price=None,
                        return_pct=None,
                        status='open'
                    )
                    trades.append(trade)
        
        # Close any remaining open trades at end date
        for trade in trades:
            if trade.status == 'open':
                exit_result = self._check_exit(trade, end_date, force_exit=True)
                if exit_result:
                    trade.exit_date = exit_result['exit_date']
                    trade.exit_price = exit_result['exit_price']
                    trade.return_pct = exit_result['return_pct']
                    trade.status = exit_result['status']
        
        # Calculate metrics
        return self._calculate_metrics(trades, strategy_name, equity_curve)
    
    def _get_historical_signal(
        self,
        symbol: str,
        strategy_name: str,
        date: datetime,
        mode: str
    ) -> Optional[Dict]:
        """Get trading signal for a specific date in the past"""
        try:
            # Fetch data up to the date (simulate what we would have known then)
            days_back = 60 if mode == 'swing' else 5
            period_start = date - timedelta(days=days_back)
            
            # Get daily data
            daily_df = self.fetcher.get_stock_data(
                symbol,
                period=f"{days_back}d",
                interval="1d"
            )
            
            if daily_df is None or len(daily_df) < 20:
                return None
            
            # Filter data to only include dates up to the signal date
            if 'datetime' in daily_df.columns:
                daily_df = daily_df[daily_df['datetime'] <= date]
            
            if len(daily_df) < 20:
                return None
            
            # Run strategy analysis
            if strategy_name == 'MOMENTUM_SWING':
                signal = self.momentum.analyze(symbol, daily_df, None)
            elif strategy_name == 'VWAP_PULLBACK':
                # For swing mode, use daily data
                signal = self.vwap.analyze(symbol, None, daily_df, None)
            elif strategy_name == 'ORB':
                # ORB needs intraday data, skip for swing backtest
                return None
            elif strategy_name == 'HVB':
                signal = self.hvb.analyze(symbol, daily_df, None, None)
            elif strategy_name == 'EARNINGS_DRIFT':
                signal = self.earnings.analyze(symbol, daily_df, None)
            else:
                return None
            
            return signal
        
        except Exception as e:
            return None
    
    def _check_exit(
        self,
        trade: Trade,
        current_date: datetime,
        force_exit: bool = False
    ) -> Optional[Dict]:
        """Check if trade should be exited"""
        try:
            # Get current price
            daily_df = self.fetcher.get_stock_data(
                trade.symbol,
                period="5d",
                interval="1d"
            )
            
            if daily_df is None or daily_df.empty:
                if force_exit:
                    # Use entry price as exit if we can't get data
                    return {
                        'exit_date': current_date,
                        'exit_price': trade.entry_price,
                        'return_pct': 0.0,
                        'status': 'breakeven'
                    }
                return None
            
            current_price = daily_df['close'].iloc[-1]
            
            # Check stop loss
            if current_price <= trade.stop_loss:
                return_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                return {
                    'exit_date': current_date,
                    'exit_price': current_price,
                    'return_pct': return_pct,
                    'status': 'loss'
                }
            
            # Check target
            if current_price >= trade.target_price:
                return_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                return {
                    'exit_date': current_date,
                    'exit_price': current_price,
                    'return_pct': return_pct,
                    'status': 'win'
                }
            
            # Force exit at end of backtest
            if force_exit:
                return_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
                if return_pct > 0:
                    status = 'win'
                elif return_pct < 0:
                    status = 'loss'
                else:
                    status = 'breakeven'
                
                return {
                    'exit_date': current_date,
                    'exit_price': current_price,
                    'return_pct': return_pct,
                    'status': status
                }
            
            return None
        
        except Exception:
            return None
    
    def _calculate_metrics(
        self,
        trades: List[Trade],
        strategy_name: str,
        equity_curve: List[Dict]
    ) -> BacktestResult:
        """Calculate backtest performance metrics"""
        if not trades:
            return BacktestResult(
                strategy=strategy_name,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                expectancy=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                best_trade=0.0,
                worst_trade=0.0
            )
        
        # Filter closed trades
        closed_trades = [t for t in trades if t.status in ['win', 'loss', 'breakeven']]
        
        if not closed_trades:
            return BacktestResult(
                strategy=strategy_name,
                total_trades=len(trades),
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                expectancy=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                best_trade=0.0,
                worst_trade=0.0
            )
        
        # Basic stats
        winning_trades = [t for t in closed_trades if t.status == 'win' and t.return_pct and t.return_pct > 0]
        losing_trades = [t for t in closed_trades if t.status == 'loss' and t.return_pct and t.return_pct < 0]
        
        total_trades = len(closed_trades)
        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        
        # Average win/loss
        avg_win = np.mean([t.return_pct for t in winning_trades]) if winning_trades else 0.0
        avg_loss = np.mean([t.return_pct for t in losing_trades]) if losing_trades else 0.0
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        
        # Total return
        returns = [t.return_pct for t in closed_trades if t.return_pct is not None]
        total_return = sum(returns) if returns else 0.0
        
        # Best/worst trade
        best_trade = max(returns) if returns else 0.0
        worst_trade = min(returns) if returns else 0.0
        
        # Profit factor
        total_wins = sum([t.return_pct for t in winning_trades]) if winning_trades else 0.0
        total_losses = abs(sum([t.return_pct for t in losing_trades])) if losing_trades else 1.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        # Max drawdown
        if equity_curve:
            equity_values = [e['equity'] for e in equity_curve]
            peak = equity_values[0]
            max_dd = 0.0
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                dd = ((peak - equity) / peak) * 100
                if dd > max_dd:
                    max_dd = dd
        else:
            max_dd = 0.0
        
        # Sharpe ratio (simplified)
        if equity_curve and len(equity_curve) > 1:
            returns_series = [e['return_pct'] for e in equity_curve if e['return_pct']]
            if returns_series and len(returns_series) > 1:
                mean_return = np.mean(returns_series)
                std_return = np.std(returns_series)
                sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        return BacktestResult(
            strategy=strategy_name,
            total_trades=total_trades,
            winning_trades=wins,
            losing_trades=losses,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            expectancy=expectancy,
            total_return=total_return,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            best_trade=best_trade,
            worst_trade=worst_trade
        )
    
    def compare_strategies(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        mode: str = "swing"
    ) -> Dict[str, BacktestResult]:
        """Compare all strategies"""
        strategies = ['MOMENTUM_SWING', 'VWAP_PULLBACK', 'HVB', 'EARNINGS_DRIFT']
        results = {}
        
        for strategy in strategies:
            try:
                result = self.backtest_strategy(strategy, symbols, start_date, end_date, mode)
                results[strategy] = result
            except Exception as e:
                print(f"⚠️  Error backtesting {strategy}: {e}")
        
        return results

