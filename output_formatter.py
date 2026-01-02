"""
AI-Powered Stock Discovery Tool - Output Formatter
"""

from typing import List, Dict


class OutputFormatter:
    """Format scanner results for display"""
    
    @staticmethod
    def format_picks(picks: List[Dict], date: str) -> str:
        """Format top picks in required format"""
        if not picks:
            return "❌ No actionable setups today (min conviction 75/100 not met)"
        
        output = [f"\n{'='*70}"]
        output.append(f"📊 TOP {len(picks)} STOCKS - {date}")
        output.append(f"{'='*70}\n")
        
        for i, pick in enumerate(picks, 1):
            risk_label = pick.get('risk_label', 'Medium Risk')
            if pick['risk_score'] > 70 and 'risk_label' not in pick:
                risk_label = 'High Risk'
            
            symbol_clean = pick['symbol'].replace('.NS', '')
            
            entry = pick['entry_price']
            sl = pick['stop_loss']
            target = pick['target_price']
            conviction = pick['conviction_score']
            strategy = pick['strategy']
            
            # Calculate position value
            position_value = pick['position_size'] * entry
            
            # Risk/Reward ratio
            risk_amount = abs(entry - sl)
            reward_amount = abs(target - entry)
            rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            output.append(f"{i}. {symbol_clean} - {strategy}")
            output.append(f"   Conviction: {conviction:.1f}/100 | Risk: {risk_label}")
            output.append(f"   Entry: ₹{entry:.2f} | SL: ₹{sl:.2f} | Target: ₹{target:.2f}")
            # Get currency symbol from pick (default to ₹ for Indian stocks)
            currency = pick.get('currency_symbol', '₹')
            output.append(f"   Position Size: {currency}{position_value:.0f} ({pick['position_size']:.0f} shares)")
            output.append(f"   Risk/Reward: 1:{rr_ratio:.2f}")
            
            # Show fundamental metrics if available
            fundamental_metrics = pick.get('fundamental_metrics', {})
            fundamental_score = pick.get('fundamental_score')
            if fundamental_metrics or fundamental_score:
                fund_summary = OutputFormatter._format_fundamental_summary(fundamental_metrics, fundamental_score)
                if fund_summary:
                    output.append(f"   📊 Fundamentals: {fund_summary}")
            
            output.append(f"   Setup: {OutputFormatter._generate_reason(pick)}")
            
            # Show learning adjustments if any
            if 'learning_adjustments' in pick and pick['learning_adjustments']:
                output.append(f"   🧠 Learning Adjustments:")
                for adj in pick['learning_adjustments']:
                    output.append(f"      • {adj}")
                if 'original_conviction' in pick:
                    orig = pick['original_conviction']
                    diff = conviction - orig
                    output.append(f"      Original score: {orig:.1f} → Adjusted: {conviction:.1f} ({diff:+.1f})")
            
            output.append("")  # Blank line between picks
        
        return "\n".join(output)
    
    @staticmethod
    def _generate_reason(pick: Dict) -> str:
        """Generate human-readable reason"""
        strategy = pick['strategy']
        features = pick.get('features', {})
        
        if strategy == 'ORB':
            surge = "strong volume" if features.get('volume_surge') else "moderate volume"
            return f"Breakout above opening range with {surge}"
        
        elif strategy == 'VWAP_PULLBACK':
            uptrend = "confirmed uptrend" if features.get('uptrend') else "consolidating"
            dist = features.get('distance_from_vwap_pct', 0)
            return f"Price {dist:.2f}% from VWAP, {uptrend}"
        
        elif strategy == 'MOMENTUM_SWING':
            rsi = features.get('rsi', 50)
            vol_trend = "rising" if features.get('volume_trend_up') else "declining"
            return f"MA crossover, RSI {rsi:.0f}, {vol_trend} volume"
        
        elif strategy == 'HVB':
            vol_pct = features.get('volatility_percentile', 0)
            potential = features.get('potential_move_pct', 0)
            return f"⚠️ High volatility ({vol_pct:.0f}th percentile), potential {potential:.1f}% move - EXPECT LARGE SWINGS"
        
        return "Technical setup confirmed"
    
    @staticmethod
    def _format_fundamental_summary(metrics: Dict, score: Optional[float] = None) -> str:
        """Format fundamental metrics summary"""
        parts = []
        
        if score is not None:
            parts.append(f"Score: {score:.1f}/100")
        
        pe = metrics.get('pe_ratio')
        if pe and pe > 0:
            parts.append(f"P/E: {pe:.1f}")
        
        pb = metrics.get('pb_ratio')
        if pb and pb > 0:
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
            parts.append(f"Rev: {growth_pct:+.1f}%")
        
        return " | ".join(parts) if parts else ""
    
    @staticmethod
    def format_feedback_prompt(picks: List[Dict]) -> str:
        """Format feedback instructions"""
        if not picks:
            return ""
        
        output = ["\n" + "="*70]
        output.append("📝 FEEDBACK INSTRUCTIONS")
        output.append("="*70 + "\n")
        output.append("After executing/reviewing these picks, provide feedback using:")
        output.append("\nCommand format:")
        output.append("  python main.py feedback --pick-id <id> --took <yes/no> --rating <1-5> --note <optional>")
        output.append("\nExample:")
        output.append(f"  python main.py feedback --pick-id {picks[0]['pick_id']} --took yes --rating 4 --note 'Good entry'")
        output.append("\nPick IDs for today:")
        for pick in picks:
            output.append(f"  • {pick['pick_id']} ({pick['symbol'].replace('.NS', '')})")
        output.append("")
        
        return "\n".join(output)
    
    @staticmethod
    def format_review(period: str = "week") -> str:
        """Format performance review with comprehensive metrics"""
        from database import PickLedger
        from datetime import datetime, timedelta
        import sqlite3
        import numpy as np
        
        ledger = PickLedger()
        db = sqlite3.connect(ledger.db_path)
        cursor = db.cursor()
        
        # Calculate date range
        if period == "day":
            days_back = 1
        elif period == "week":
            days_back = 7
        elif period == "month":
            days_back = 30
        else:
            days_back = 7
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Get picks with outcomes in period
        cursor.execute("""
            SELECT p.strategy, p.market_regime, o.final_return, o.hit_target, o.hit_stop,
                   o.mfe, o.mae, f.took_trade, f.rating
            FROM picks p
            JOIN outcomes o ON p.pick_id = o.pick_id
            LEFT JOIN feedback f ON p.pick_id = f.pick_id
            WHERE p.timestamp >= ?
            ORDER BY p.timestamp DESC
        """, (cutoff_date,))
        
        results = cursor.fetchall()
        db.close()
        
        if not results:
            return f"\n📈 PERFORMANCE REVIEW - Last {period}\n{'='*70}\n\nNo picks with outcomes in this period."
        
        # Calculate metrics
        returns = [r[2] for r in results if r[2] is not None]
        wins = [r for r in results if r[2] is not None and r[2] > 0]
        losses = [r for r in results if r[2] is not None and r[2] <= 0]
        hit_targets = sum(1 for r in results if r[3])
        hit_stops = sum(1 for r in results if r[4])
        
        total_picks = len(results)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_picks * 100) if total_picks > 0 else 0
        
        avg_return = np.mean(returns) if returns else 0
        avg_win = np.mean([r[2] for r in wins]) if wins else 0
        avg_loss = np.mean([r[2] for r in losses]) if losses else 0
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss) if total_picks > 0 else 0
        
        # Max drawdown (from MFE/MAE)
        mae_values = [r[5] for r in results if r[5] is not None]
        max_drawdown = min(mae_values) if mae_values else 0
        
        # Sharpe-like ratio (simplified: avg return / std dev)
        std_return = np.std(returns) if len(returns) > 1 else 1
        sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        
        # By strategy
        strategy_stats = {}
        for strategy in ['ORB', 'VWAP_PULLBACK', 'MOMENTUM_SWING', 'HVB']:
            strat_results = [r for r in results if r[0] == strategy]
            if strat_results:
                strat_returns = [r[2] for r in strat_results if r[2] is not None]
                strat_wins = len([r for r in strat_results if r[2] is not None and r[2] > 0])
                strategy_stats[strategy] = {
                    'count': len(strat_results),
                    'win_rate': (strat_wins / len(strat_results) * 100) if strat_results else 0,
                    'avg_return': np.mean(strat_returns) if strat_returns else 0
                }
        
        # Format output
        output = [f"\n📈 PERFORMANCE REVIEW - Last {period}"]
        output.append("="*70)
        output.append(f"\nTotal Picks: {total_picks}")
        output.append(f"Win Rate: {win_rate:.1f}% ({win_count}W / {loss_count}L)")
        output.append(f"Average Return: {avg_return:.2f}%")
        output.append(f"Average Win: {avg_win:.2f}%")
        output.append(f"Average Loss: {avg_loss:.2f}%")
        output.append(f"Expectancy: {expectancy:.2f}%")
        output.append(f"Max Drawdown: {max_drawdown:.2f}%")
        output.append(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        output.append(f"Targets Hit: {hit_targets} | Stops Hit: {hit_stops}")
        
        if strategy_stats:
            output.append("\nBy Strategy:")
            for strategy, stats in strategy_stats.items():
                output.append(f"  {strategy}: {stats['count']} picks, {stats['win_rate']:.1f}% win rate, {stats['avg_return']:.2f}% avg return")
        
        return "\n".join(output)
