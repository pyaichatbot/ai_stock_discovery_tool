"""
AI-Powered Stock Discovery Tool - Main Entry Point
Complete with scanning, feedback, and outcome computation
"""

import sys
import argparse
from datetime import datetime

import sys
import os
# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_discovery.config import Config
from stock_discovery.config_manager import ConfigManager
from stock_discovery.scanner_engine import ScannerEngine
from stock_discovery.output_formatter import OutputFormatter
from stock_discovery.database import PickLedger
from stock_discovery.scheduler import AutomationScheduler
from stock_discovery.backtesting import BacktestingEngine
from stock_discovery.multi_timeframe import MultiTimeframeAnalyzer


def cmd_scan(args, config: Config):
    """Run market scan with smart configuration"""
    # Get flags
    enable_hvb = args.hvb
    enable_penny_stock = args.penny_stock if hasattr(args, 'penny_stock') else False
    profile = getattr(args, 'profile', None)
    
    # Smart configuration: Auto-configure based on flags
    # This allows using --penny-stock without changing code!
    if enable_penny_stock or enable_hvb or profile:
        config = ConfigManager.create_config(
            profile=profile,
            enable_penny_stock=enable_penny_stock,
            enable_hvb=enable_hvb
        )
    
    # Apply command-line config overrides
    config_overrides = {}
    if hasattr(args, 'min_conviction') and args.min_conviction is not None:
        config.MIN_CONVICTION_SCORE = args.min_conviction
        print(f"🔧 Override: MIN_CONVICTION_SCORE = {args.min_conviction}")
    
    if hasattr(args, 'max_positions') and args.max_positions is not None:
        config.MAX_CONCURRENT_POSITIONS = args.max_positions
        print(f"🔧 Override: MAX_CONCURRENT_POSITIONS = {args.max_positions}")
    
    if hasattr(args, 'min_volume') and args.min_volume is not None:
        config.MIN_AVG_VOLUME = args.min_volume
        print(f"🔧 Override: MIN_AVG_VOLUME = {args.min_volume}")
    
    if hasattr(args, 'min_price') and args.min_price is not None:
        config.MIN_PRICE = args.min_price
        print(f"🔧 Override: MIN_PRICE = {args.min_price}")
    
    if hasattr(args, 'max_price') and args.max_price is not None:
        config.MAX_PRICE = args.max_price
        print(f"🔧 Override: MAX_PRICE = {args.max_price}")
    
    if hasattr(args, 'top_n') and args.top_n is not None:
        config.TOP_N_PICKS = args.top_n
        print(f"🔧 Override: TOP_N_PICKS = {args.top_n}")
    
    if hasattr(args, 'ignore_position_limit') and args.ignore_position_limit:
        config.MAX_CONCURRENT_POSITIONS = 999  # Effectively disable limit
        print("🔧 Override: Ignoring position limit (MAX_CONCURRENT_POSITIONS = 999)")
    
    if any([hasattr(args, k) and getattr(args, k) is not None 
            for k in ['min_conviction', 'max_positions', 'min_volume', 'min_price', 'max_price', 'top_n']]) or \
       (hasattr(args, 'ignore_position_limit') and args.ignore_position_limit):
        print()
    
    scanner = ScannerEngine(config)
    formatter = OutputFormatter()
    
    mode = args.mode
    
    if enable_hvb:
        print("⚠️  HIGH RISK MODE ENABLED - HVB picks will be included")
        print("   This mode can produce 10-30%+ moves but with HIGH VOLATILITY")
        print()
    
    # Run scan
    picks = scanner.scan_market(mode=mode, enable_hvb=enable_hvb, enable_penny_stock=enable_penny_stock)
    
    # Format and display
    date_str = datetime.now().strftime("%b %d, %Y")
    output = formatter.format_picks(picks, date_str)
    print(output)
    
    if picks:
        print(f"\n✅ {len(picks)} picks saved to ledger")
        
        # Show feedback prompt
        feedback_prompt = formatter.format_feedback_prompt(picks)
        print(feedback_prompt)
    else:
        print("\n⚠️  No picks generated today")
        print("   Possible reasons:")
        print("   • Market regime not favorable")
        print("   • No stocks met minimum conviction threshold (75)")
        print("   • Adjust filters in config.py if needed")


def cmd_feedback(args):
    """Add feedback for a pick"""
    ledger = PickLedger()
    
    pick_id = args.pick_id
    took = args.took.lower() == 'yes'
    rating = args.rating
    notes = args.note or ""
    rejection_reason = args.reject_reason or ""
    
    if not took and not rejection_reason:
        print("⚠️  For rejected picks, please provide --reject-reason")
        print("   Examples: 'too_risky', 'unclear_catalyst', 'low_liquidity', 'better_setup_elsewhere'")
        return
    
    if rating < 1 or rating > 5:
        print("❌ Rating must be between 1 and 5")
        return
    
    ledger.add_feedback(pick_id, took, rating, notes, rejection_reason)
    
    print(f"✅ Feedback saved for {pick_id}")
    print(f"   Took trade: {'Yes' if took else 'No'}")
    print(f"   Rating: {rating}/5")
    if notes:
        print(f"   Notes: {notes}")
    if rejection_reason:
        print(f"   Rejection reason: {rejection_reason}")


def cmd_compute_outcomes(args, config: Config):
    """Compute outcomes for pending picks"""
    scanner = ScannerEngine(config)
    
    print("🔄 Computing outcomes for pending picks...")
    print("   This updates the learning system based on realized results")
    print()
    
    scanner.compute_outcomes_for_pending_picks()
    
    print("\n✅ Outcomes computed and learning updated")


def cmd_review(args):
    """Show performance review"""
    formatter = OutputFormatter()
    period = args.period
    
    output = formatter.format_review(period)
    print(output)


def cmd_positions(args):
    """View and manage active positions"""
    from datetime import datetime
    ledger = PickLedger()
    
    if args.clear_all:
        # Clear all pending positions by adding dummy outcomes
        pending = ledger.get_picks_without_outcomes()
        if not pending:
            print("✅ No pending positions to clear")
            return
        
        confirm = input(f"⚠️  Are you sure you want to clear {len(pending)} pending positions? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        for pick in pending:
            ledger.save_outcome(pick['pick_id'], 0.0, 0.0, 0.0, False, False)
        print(f"✅ Cleared {len(pending)} pending positions")
        return
    
    if args.clear_old:
        # Mark old positions (>30 days) as inactive
        pending = ledger.get_picks_without_outcomes()
        old_count = 0
        for pick in pending:
            pick_time = datetime.fromisoformat(pick['timestamp'])
            days_old = (datetime.now() - pick_time).days
            if days_old > 30:
                ledger.save_outcome(pick['pick_id'], 0.0, 0.0, 0.0, False, False)
                old_count += 1
        
        if old_count > 0:
            print(f"✅ Cleared {old_count} old positions (>30 days)")
        else:
            print("✅ No old positions to clear")
        return
    
    # Default: list active positions
    pending = ledger.get_picks_without_outcomes()
    
    if not pending:
        print("✅ No active positions")
        return
    
    print("=" * 70)
    print(f"📊 ACTIVE POSITIONS ({len(pending)})")
    print("=" * 70)
    print()
    
    # Group by strategy and count by age
    intraday_count = 0
    swing_count = 0
    
    for pick in pending:
        pick_time = datetime.fromisoformat(pick['timestamp'])
        days_old = (datetime.now() - pick_time).days
        
        symbol = pick['symbol'].replace('.NS', '')
        strategy = pick['strategy']
        entry = pick['entry_price']
        sl = pick['stop_loss']
        target = pick['target_price']
        
        if strategy in ['ORB', 'VWAP_PULLBACK']:
            if days_old <= 1:
                intraday_count += 1
        else:
            if days_old <= 30:
                swing_count += 1
        
        age_str = f"{days_old} days" if days_old > 0 else "Today"
        print(f"• {symbol} - {strategy} ({age_str})")
        print(f"  Entry: ₹{entry:.2f} | SL: ₹{sl:.2f} | Target: ₹{target:.2f}")
        print()
    
    print("=" * 70)
    print(f"Active: {intraday_count + swing_count} (Intraday: {intraday_count}, Swing: {swing_count})")
    print(f"Max allowed: {Config().MAX_CONCURRENT_POSITIONS}")
    print("=" * 70)
    print()
    print("💡 Tips:")
    print("  • Use --clear-old to mark positions >30 days as inactive")
    print("  • Use --clear-all to clear all pending positions (use with caution)")
    print("  • Use --max-positions N to override the limit for next scan")


def cmd_schedule(args, config: Config):
    """Manage automation scheduler"""
    scheduler = AutomationScheduler(config)
    action = args.schedule_action
    
    if action == 'enable':
        scheduler.start()
    elif action == 'disable':
        scheduler.stop()
    elif action == 'status':
        scheduler.status()
    else:
        print("⚠️  Unknown schedule action. Use: enable, disable, or status")


def cmd_backtest(args, config: Config):
    """Run backtesting on strategies"""
    from datetime import datetime, timedelta
    from stock_discovery.symbol_loader import load_nifty50
    
    # Parse period
    period_str = args.period.lower()
    if period_str.endswith('y'):
        years = int(period_str[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
    elif period_str.endswith('m'):
        months = int(period_str[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
    else:
        print("❌ Invalid period format. Use: 1y, 2y, 6m, etc.")
        return
    
    # Get symbols
    if args.symbols:
        symbols = [s if '.NS' in s else f"{s}.NS" for s in args.symbols]
    else:
        symbols = load_nifty50()[:10]  # Use first 10 for faster backtest
    
    # Initialize backtesting engine
    engine = BacktestingEngine(config)
    
    if args.strategy and args.strategy != 'all':
        # Backtest single strategy
        print(f"🔄 Backtesting {args.strategy}...")
        result = engine.backtest_strategy(
            args.strategy.upper(),
            symbols,
            start_date,
            end_date,
            args.mode
        )
        
        # Format and display results
        from output_formatter import OutputFormatter
        output = OutputFormatter.format_backtest_result(result)
        print(output)
    else:
        # Compare all strategies
        print(f"🔄 Comparing all strategies...")
        results = engine.compare_strategies(symbols, start_date, end_date, args.mode)
        
        # Format and display comparison
        from output_formatter import OutputFormatter
        output = OutputFormatter.format_backtest_comparison(results)
        print(output)


def main():
    """Main entry point with CLI argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='AI-Powered Stock Discovery Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run intraday scan
  python main.py scan --mode intraday
  
  # Run with config overrides
  python main.py scan --mode intraday --min-conviction 55 --max-positions 10
  
  # Run swing scan with HVB mode
  python main.py scan --mode swing --hvb
  
  # View active positions
  python main.py positions
  
  # Clear old positions (>30 days)
  python main.py positions --clear-old
  
  # Add feedback
  python main.py feedback --pick-id REL_20241230_1000 --took yes --rating 4 --note "Good setup"
  
  # Compute outcomes (run after market close)
  python main.py compute-outcomes
  
  # Review performance
  python main.py review --period week
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan market for opportunities')
    scan_parser.add_argument('--mode', choices=['intraday', 'swing'], default='intraday',
                            help='Trading mode (default: intraday)')
    scan_parser.add_argument('--hvb', action='store_true',
                            help='Enable HIGH RISK HVB mode (opt-in)')
    scan_parser.add_argument('--penny-stock', action='store_true',
                            help='Enable Penny Stock mode (auto-configures: smallcap250, lower threshold)')
    scan_parser.add_argument('--profile', choices=['normal', 'penny_stock', 'hvb', 'aggressive', 'conservative'],
                            help='Use preset configuration profile (overrides other flags)')
    
    # Config override arguments
    scan_parser.add_argument('--min-conviction', type=float, metavar='SCORE',
                            help='Override MIN_CONVICTION_SCORE (default: 60.0)')
    scan_parser.add_argument('--max-positions', type=int, metavar='N',
                            help='Override MAX_CONCURRENT_POSITIONS (default: 5)')
    scan_parser.add_argument('--min-volume', type=int, metavar='VOLUME',
                            help='Override MIN_AVG_VOLUME (default: 100000)')
    scan_parser.add_argument('--min-price', type=float, metavar='PRICE',
                            help='Override MIN_PRICE (default: 50.0)')
    scan_parser.add_argument('--max-price', type=float, metavar='PRICE',
                            help='Override MAX_PRICE (default: 5000.0)')
    scan_parser.add_argument('--top-n', type=int, metavar='N',
                            help='Override TOP_N_PICKS (default: 3)')
    scan_parser.add_argument('--ignore-position-limit', action='store_true',
                            help='Ignore max concurrent positions limit (use with caution)')
    
    # Feedback command
    feedback_parser = subparsers.add_parser('feedback', help='Add feedback for a pick')
    feedback_parser.add_argument('--pick-id', required=True, help='Pick ID')
    feedback_parser.add_argument('--took', required=True, choices=['yes', 'no'],
                                help='Did you take this trade?')
    feedback_parser.add_argument('--rating', type=int, required=True,
                                help='Rating 1-5')
    feedback_parser.add_argument('--note', help='Optional notes')
    feedback_parser.add_argument('--reject-reason', 
                                help='Reason for rejection (if not taken)')
    
    # Compute outcomes command
    compute_parser = subparsers.add_parser('compute-outcomes',
                                          help='Compute outcomes for pending picks')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Performance review')
    review_parser.add_argument('--period', choices=['day', 'week', 'month'],
                              default='week', help='Review period')
    
    # Positions command - view and manage active positions
    positions_parser = subparsers.add_parser('positions', help='View and manage active positions')
    positions_parser.add_argument('--list', action='store_true', default=True,
                                 help='List active positions (default action)')
    positions_parser.add_argument('--clear-old', action='store_true',
                                 help='Mark old positions (>30 days) as inactive')
    positions_parser.add_argument('--clear-all', action='store_true',
                                 help='⚠️  Clear ALL pending positions (use with caution)')
    
    # Schedule command
    parser_schedule = subparsers.add_parser('schedule', help='Automation scheduling')
    schedule_subparsers = parser_schedule.add_subparsers(dest='schedule_action', help='Schedule action')
    
    schedule_subparsers.add_parser('enable', help='Enable automation scheduler')
    schedule_subparsers.add_parser('disable', help='Disable automation scheduler')
    schedule_subparsers.add_parser('status', help='Show scheduler status')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Backtest strategies on historical data')
    backtest_parser.add_argument('--strategy', choices=['ORB', 'VWAP_PULLBACK', 'MOMENTUM_SWING', 'HVB', 'EARNINGS_DRIFT', 'all'],
                                 default='all', help='Strategy to backtest (default: all)')
    backtest_parser.add_argument('--period', default='1y', help='Backtest period (e.g., 1y, 2y, 6m)')
    backtest_parser.add_argument('--mode', choices=['intraday', 'swing'], default='swing',
                                 help='Trading mode (default: swing)')
    backtest_parser.add_argument('--symbols', nargs='+', help='Specific symbols to test (default: NIFTY50 first 10)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load base config (will be overridden by smart config if needed)
    config = Config()
    
    # Route to command
    if args.command == 'scan':
        cmd_scan(args, config)
    elif args.command == 'feedback':
        cmd_feedback(args)
    elif args.command == 'compute-outcomes':
        cmd_compute_outcomes(args, config)
    elif args.command == 'review':
        cmd_review(args)
    elif args.command == 'positions':
        cmd_positions(args)
    elif args.command == 'schedule':
        cmd_schedule(args, config)
    elif args.command == 'backtest':
        cmd_backtest(args, config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
