#!/usr/bin/env python3
"""
Daily Stocks Preset Script
Generates today's top 3 regular stocks and saves to daily folder
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

from config import Config
from scanner_engine import ScannerEngine
from output_formatter import OutputFormatter


def create_daily_folder() -> Path:
    """Create daily folder structure: daily_picks/YYYY-MM-DD/"""
    today = datetime.now()
    folder_name = today.strftime("%Y-%m-%d")
    daily_folder = Path("daily_picks") / folder_name
    daily_folder.mkdir(parents=True, exist_ok=True)
    return daily_folder


def save_text_output(picks: list, folder: Path, filename: str = "today_stocks.txt"):
    """Save picks in human-readable text format"""
    filepath = folder / filename
    date_str = datetime.now().strftime("%b %d, %Y")
    
    if not picks:
        content = f"""
{'='*70}
📊 TOP 3 STOCKS - {date_str}
{'='*70}

❌ No actionable setups today (min conviction threshold not met)

Possible reasons:
• Market regime not favorable
• No stocks met minimum conviction threshold
• Risk management limits reached
• Adjust filters in config.py if needed
"""
    else:
        formatter = OutputFormatter()
        content = formatter.format_picks(picks, date_str)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Text output saved: {filepath}")


def save_json_output(picks: list, folder: Path, filename: str = "today_stocks.json"):
    """Save picks in JSON format for programmatic access"""
    filepath = folder / filename
    
    # Prepare JSON-serializable data
    json_data = {
        'date': datetime.now().isoformat(),
        'date_readable': datetime.now().strftime("%b %d, %Y"),
        'count': len(picks),
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
            'is_penny_stock': pick.get('is_penny_stock', False),
        }
        
        # Calculate risk/reward
        entry = pick.get('entry_price', 0)
        sl = pick.get('stop_loss', 0)
        target = pick.get('target_price', 0)
        if entry and sl and target:
            risk_amount = abs(entry - sl)
            reward_amount = abs(target - entry)
            pick_data['risk_reward_ratio'] = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Add features if available
        if 'features' in pick:
            pick_data['features'] = pick.get('features', {})
        
        json_data['picks'].append(pick_data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON output saved: {filepath}")


def main():
    """Main execution"""
    try:
        print("=" * 70)
        print("📊 DAILY STOCKS PRESET - Generating Today's Top 3 Stocks")
        print("=" * 70)
        print()
        
        # Create daily folder
        daily_folder = create_daily_folder()
        print(f"📁 Daily folder: {daily_folder}")
        print()
        
        # Initialize with default config
        config = Config()
        scanner = ScannerEngine(config)
        
        # Run scan (intraday mode, regular stocks)
        print("🔍 Scanning market for regular stocks...")
        picks = scanner.scan_market(mode='intraday', enable_hvb=False, enable_penny_stock=False)
        
        # Limit to top 3
        picks = picks[:3]
        
        print(f"\n📈 Found {len(picks)} picks")
        
        # Save outputs
        save_text_output(picks, daily_folder, "today_stocks.txt")
        save_json_output(picks, daily_folder, "today_stocks.json")
        
        if picks:
            print(f"\n✅ Successfully saved {len(picks)} stock picks")
            print(f"   Location: {daily_folder}")
        else:
            print("\n⚠️  No picks generated today")
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

