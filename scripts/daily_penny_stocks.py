#!/usr/bin/env python3
"""
Daily Penny Stocks Preset Script
Generates today's top 3 penny stocks and saves to daily folder
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_discovery.config import Config
from stock_discovery.config_manager import ConfigManager
from stock_discovery.scanner_engine import ScannerEngine
from stock_discovery.output_formatter import OutputFormatter
from stock_discovery.database import PickLedger


def create_daily_folder() -> Path:
    """Create daily folder structure: daily_picks/YYYY-MM-DD/"""
    today = datetime.now()
    folder_name = today.strftime("%Y-%m-%d")
    # Create in project root (parent of scripts/)
    project_root = Path(__file__).parent.parent
    daily_folder = project_root / "daily_picks" / folder_name
    daily_folder.mkdir(parents=True, exist_ok=True)
    return daily_folder


def save_text_output(picks: list, folder: Path, filename: str = "today_penny_stocks.txt"):
    """Save picks in human-readable text format"""
    filepath = folder / filename
    date_str = datetime.now().strftime("%b %d, %Y")
    
    if not picks:
        content = f"""
{'='*70}
📊 TOP 3 PENNY STOCKS - {date_str}
{'='*70}

⚠️  PENNY STOCK MODE - HIGH RISK

❌ No actionable penny stock setups today (min conviction threshold not met)

Possible reasons:
• Market regime not favorable
• No penny stocks met minimum conviction threshold
• Risk management limits reached
• Penny stock filters too strict
"""
    else:
        formatter = OutputFormatter()
        content = formatter.format_picks(picks, date_str)
        
        # Add penny stock warning header
        header = f"""
{'='*70}
📊 TOP {len(picks)} PENNY STOCKS - {date_str}
{'='*70}

⚠️  PENNY STOCK MODE - HIGH RISK
   • Stocks priced ₹1-50 only
   • Higher volatility and manipulation risk
   • Stricter position limits applied
   • Use with extreme caution!

"""
        content = header + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Text output saved: {filepath}")


def save_json_output(picks: list, folder: Path, filename: str = "today_penny_stocks.json"):
    """Save picks in JSON format for programmatic access"""
    filepath = folder / filename
    
    # Prepare JSON-serializable data
    json_data = {
        'date': datetime.now().isoformat(),
        'date_readable': datetime.now().strftime("%b %d, %Y"),
        'count': len(picks),
        'mode': 'penny_stock',
        'warning': 'HIGH RISK - Penny stocks are highly volatile and carry significant risk',
        'picks': []
    }
    
    for pick in picks:
        pick_data = {
            'pick_id': pick.get('pick_id'),
            'symbol': pick.get('symbol', '').replace('.NS', ''),
            'symbol_full': pick.get('symbol'),
            'strategy': pick.get('strategy'),
            'conviction_score': pick.get('conviction_score'),
            'risk_score': pick.get('risk_score'),
            'entry_price': pick.get('entry_price'),
            'stop_loss': pick.get('stop_loss'),
            'target_price': pick.get('target_price'),
            'position_size': pick.get('position_size'),
            'position_value': pick.get('position_size', 0) * pick.get('entry_price', 0),
            'timestamp': pick.get('timestamp'),
            'market_regime': pick.get('market_regime'),
            'is_penny_stock': True,  # Always True for penny stock script
        }
        
        # Calculate risk/reward
        entry = pick.get('entry_price', 0)
        sl = pick.get('stop_loss', 0)
        target = pick.get('target_price', 0)
        if entry and sl and target:
            risk_amount = abs(entry - sl)
            reward_amount = abs(target - entry)
            pick_data['risk_reward_ratio'] = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Add features if available (convert to JSON-serializable format)
        if 'features' in pick:
            features = pick.get('features', {})
            # Convert numpy types and other non-serializable types
            import numpy as np
            serializable_features = {}
            for k, v in features.items():
                if isinstance(v, (np.integer, np.int64)):
                    serializable_features[k] = int(v)
                elif isinstance(v, (np.floating, np.float64)):
                    serializable_features[k] = float(v)
                elif isinstance(v, np.ndarray):
                    serializable_features[k] = v.tolist()
                elif isinstance(v, (bool, int, float, str)) or v is None:
                    serializable_features[k] = v
                else:
                    serializable_features[k] = str(v)  # Fallback to string
            pick_data['features'] = serializable_features
        
        json_data['picks'].append(pick_data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON output saved: {filepath}")


def main():
    """Main execution"""
    try:
        print("=" * 70)
        print("📊 DAILY PENNY STOCKS PRESET - Generating Today's Top 3 Penny Stocks")
        print("=" * 70)
        print()
        
        print("⚠️  PENNY STOCK MODE ENABLED - HIGH RISK")
        print("   • Stocks priced ₹1-50 only")
        print("   • Higher volatility and manipulation risk")
        print("   • Stricter position limits applied")
        print("   • Use with extreme caution!")
        print()
        
        # Create daily folder
        daily_folder = create_daily_folder()
        print(f"📁 Daily folder: {daily_folder}")
        print()
        
        # Clear ALL pending positions before scanning
        # For daily scans, we want completely fresh picks each day
        # This ensures we don't hit position limits from previous scans
        ledger = PickLedger()
        pending = ledger.get_picks_without_outcomes()
        cleared_count = 0
        
        # Clear all pending positions to start fresh
        for pick in pending:
            ledger.save_outcome(pick['pick_id'], 0.0, 0.0, 0.0, False, False)
            cleared_count += 1
        
        if cleared_count > 0:
            print(f"🧹 Cleared {cleared_count} pending positions from previous scans")
            print("   (Daily scans start fresh each day)")
            print()
        
        # Initialize with penny stock config
        config = ConfigManager.create_config(enable_penny_stock=True)
        
        # Apply optimized settings for daily scans
        config.MIN_CONVICTION_SCORE = 55.0  # Lower threshold to find more opportunities
        config.MAX_CONCURRENT_POSITIONS = 10  # Higher limit for daily scans
        print(f"🔧 Using optimized settings: MIN_CONVICTION={config.MIN_CONVICTION_SCORE}, MAX_POSITIONS={config.MAX_CONCURRENT_POSITIONS}")
        print()
        
        scanner = ScannerEngine(config)
        
        # Run scan (intraday mode, penny stocks enabled)
        print("🔍 Scanning market for penny stocks...")
        picks = scanner.scan_market(mode='intraday', enable_hvb=False, enable_penny_stock=True)
        
        # Limit to top 3
        picks = picks[:3]
        
        print(f"\n📈 Found {len(picks)} penny stock picks")
        
        # Save outputs
        save_text_output(picks, daily_folder, "today_penny_stocks.txt")
        save_json_output(picks, daily_folder, "today_penny_stocks.json")
        
        if picks:
            print(f"\n✅ Successfully saved {len(picks)} penny stock picks")
            print(f"   Location: {daily_folder}")
        else:
            print("\n⚠️  No penny stock picks generated today")
            print("   Files created with empty/placeholder content")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

