"""
AI-Powered Stock Discovery Tool - Main Entry Point
Complete with scanning, feedback, and outcome computation
"""

import sys
import argparse
from datetime import datetime

from config import Config
from scanner_engine import ScannerEngine
from output_formatter import OutputFormatter
from database import PickLedger


def cmd_scan(args, config: Config):
    """Run market scan"""
    scanner = ScannerEngine(config)
    formatter = OutputFormatter()
    
    mode = args.mode
    enable_hvb = args.hvb
    
    if enable_hvb and not config.HVB_ENABLED:
        print("⚠️  HVB mode requested but not enabled in config")
        print("   Set HVB_ENABLED = True in config.py to enable")
        return
    
    if enable_hvb:
        print("⚠️  HIGH RISK MODE ENABLED - HVB picks will be included")
        print("   This mode can produce 10-30%+ moves but with HIGH VOLATILITY")
        print()
    
    # Run scan
    picks = scanner.scan_market(mode=mode, enable_hvb=enable_hvb)
    
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


def main():
    """Main entry point with CLI argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='AI-Powered Stock Discovery Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run intraday scan
  python main.py scan --mode intraday
  
  # Run swing scan with HVB mode
  python main.py scan --mode swing --hvb
  
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load config
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
