"""
AI-Powered Stock Discovery Tool - Risk Management Engine
Kill-switches, no-trade conditions, position limits
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from database import PickLedger
from config import Config


class RiskManager:
    """Risk management with kill-switches and no-trade conditions"""
    
    def __init__(self, config: Config, ledger: PickLedger):
        self.config = config
        self.ledger = ledger
    
    def check_daily_loss_threshold(self) -> Dict:
        """
        Check if daily loss threshold (kill-switch) has been hit
        
        Returns:
            Dict with 'allowed' (bool) and 'reason' (str)
        """
        # Get today's picks with outcomes
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # Get all picks from today
        conn = self.ledger.db_path
        import sqlite3
        db = sqlite3.connect(conn)
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT p.pick_id, o.final_return, p.position_size, p.entry_price
            FROM picks p
            JOIN outcomes o ON p.pick_id = o.pick_id
            WHERE DATE(p.timestamp) = DATE(?)
        """, (today_str,))
        
        results = cursor.fetchall()
        db.close()
        
        # Calculate total loss for today
        total_loss = 0.0
        for pick_id, final_return, position_size, entry_price in results:
            if final_return < 0:  # Only count losses
                loss_amount = abs(final_return / 100.0) * position_size * entry_price
                total_loss += loss_amount
        
        # Check against threshold (default 5% of total budget)
        max_daily_loss = self.config.TOTAL_BUDGET * getattr(self.config, 'MAX_DAILY_LOSS_PCT', 0.05)
        
        if total_loss >= max_daily_loss:
            return {
                'allowed': False,
                'reason': f'Daily loss threshold hit: {total_loss:.2f} >= {max_daily_loss:.2f}',
                'total_loss': total_loss,
                'threshold': max_daily_loss
            }
        
        return {
            'allowed': True,
            'reason': f'Daily loss OK: {total_loss:.2f} < {max_daily_loss:.2f}',
            'total_loss': total_loss,
            'threshold': max_daily_loss
        }
    
    def check_concurrent_positions(self) -> Dict:
        """
        Check if max concurrent positions limit is reached
        
        Returns:
            Dict with 'allowed' (bool) and 'reason' (str)
        """
        # Get active picks (picks without outcomes, within holding period)
        max_positions = getattr(self.config, 'MAX_CONCURRENT_POSITIONS', 5)
        
        # Get picks without outcomes
        pending_picks = self.ledger.get_picks_without_outcomes()
        
        # Filter to recent picks (within last 30 days for swing, last day for intraday)
        active_count = 0
        for pick in pending_picks:
            pick_time = datetime.fromisoformat(pick['timestamp'])
            days_old = (datetime.now() - pick_time).days
            
            # Determine if still active based on strategy
            if pick['strategy'] in ['ORB', 'VWAP_PULLBACK']:
                if days_old <= 1:  # Intraday strategies
                    active_count += 1
            else:
                if days_old <= 30:  # Swing strategies
                    active_count += 1
        
        if active_count >= max_positions:
            return {
                'allowed': False,
                'reason': f'Max concurrent positions reached: {active_count} >= {max_positions}',
                'current': active_count,
                'max': max_positions
            }
        
        return {
            'allowed': True,
            'reason': f'Position limit OK: {active_count} < {max_positions}',
            'current': active_count,
            'max': max_positions
        }
    
    def check_no_trade_conditions(self, symbol: str, volatility_percentile: float = None) -> Dict:
        """
        Check for no-trade conditions (volatility spikes, negative news, etc.)
        
        Args:
            symbol: Stock symbol
            volatility_percentile: Current volatility percentile
        
        Returns:
            Dict with 'allowed' (bool) and 'reason' (str)
        """
        reasons = []
        
        # Check volatility spike (if provided)
        if volatility_percentile is not None:
            max_volatility = getattr(self.config, 'MAX_VOLATILITY_PERCENTILE', 95.0)
            if volatility_percentile > max_volatility:
                reasons.append(f'Volatility too high: {volatility_percentile:.1f}% > {max_volatility:.1f}%')
        
        # Note: Negative news check is done in scanner_engine before this
        
        if reasons:
            return {
                'allowed': False,
                'reason': '; '.join(reasons),
                'conditions': reasons
            }
        
        return {
            'allowed': True,
            'reason': 'No-trade conditions OK'
        }
    
    def can_trade(self, symbol: str, volatility_percentile: float = None) -> Dict:
        """
        Comprehensive check: Can we trade this symbol?
        
        Checks:
        1. Daily loss threshold
        2. Concurrent positions
        3. No-trade conditions
        
        Returns:
            Dict with 'allowed' (bool), 'reason' (str), and details
        """
        # Check daily loss
        daily_loss_check = self.check_daily_loss_threshold()
        if not daily_loss_check['allowed']:
            return {
                'allowed': False,
                'reason': f"KILL-SWITCH: {daily_loss_check['reason']}",
                'check': 'daily_loss',
                'details': daily_loss_check
            }
        
        # Check concurrent positions
        position_check = self.check_concurrent_positions()
        if not position_check['allowed']:
            return {
                'allowed': False,
                'reason': f"Position limit: {position_check['reason']}",
                'check': 'concurrent_positions',
                'details': position_check
            }
        
        # Check no-trade conditions
        no_trade_check = self.check_no_trade_conditions(symbol, volatility_percentile)
        if not no_trade_check['allowed']:
            return {
                'allowed': False,
                'reason': f"No-trade condition: {no_trade_check['reason']}",
                'check': 'no_trade',
                'details': no_trade_check
            }
        
        return {
            'allowed': True,
            'reason': 'All risk checks passed',
            'checks': {
                'daily_loss': daily_loss_check,
                'concurrent_positions': position_check,
                'no_trade': no_trade_check
            }
        }

