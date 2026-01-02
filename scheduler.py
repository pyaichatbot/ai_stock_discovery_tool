"""
AI-Powered Stock Discovery Tool - Automation/Scheduling Module
Automated scans, refreshes, and performance reviews
"""

import schedule
import time
import threading
from datetime import datetime
from typing import Optional
from config import Config
from scanner_engine import ScannerEngine
from output_formatter import OutputFormatter
import sys


class AutomationScheduler:
    """Schedule automated scans and reviews"""
    
    def __init__(self, config: Config):
        self.config = config
        self.scanner = ScannerEngine(config)
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def pre_market_scan(self):
        """Run pre-market scan"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Pre-Market Scan")
        print("=" * 70)
        try:
            picks = self.scanner.scan_market(mode='swing', enable_hvb=False, enable_penny_stock=False)
            if picks:
                output = OutputFormatter.format_picks(picks, datetime.now().strftime('%Y-%m-%d'))
                print(output)
            else:
                print("No picks generated in pre-market scan")
        except Exception as e:
            print(f"Error in pre-market scan: {e}")
        print("=" * 70 + "\n")
    
    def intraday_refresh(self):
        """Run intraday refresh scan"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Intraday Refresh")
        print("=" * 70)
        try:
            picks = self.scanner.scan_market(mode='intraday', enable_hvb=False, enable_penny_stock=False)
            if picks:
                output = OutputFormatter.format_picks(picks, datetime.now().strftime('%Y-%m-%d'))
                print(output)
            else:
                print("No picks generated in intraday refresh")
        except Exception as e:
            print(f"Error in intraday refresh: {e}")
        print("=" * 70 + "\n")
    
    def end_of_day_summary(self):
        """Run end-of-day summary"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 End-of-Day Summary")
        print("=" * 70)
        try:
            # Compute outcomes for pending picks (via scanner)
            self.scanner.compute_outcomes_for_pending_picks()
            
            # Show performance review
            review = OutputFormatter.format_review(period='day')
            print(review)
        except Exception as e:
            print(f"Error in EOD summary: {e}")
        print("=" * 70 + "\n")
    
    def weekly_review(self):
        """Run weekly performance review"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📈 Weekly Performance Review")
        print("=" * 70)
        try:
            review = OutputFormatter.format_review(period='week')
            print(review)
        except Exception as e:
            print(f"Error in weekly review: {e}")
        print("=" * 70 + "\n")
    
    def setup_schedule(self):
        """Setup all scheduled tasks"""
        # Clear existing schedule
        schedule.clear()
        
        # Pre-market scan (9:00 AM IST)
        schedule.every().day.at(self.config.PRE_MARKET_SCAN_TIME).do(self.pre_market_scan)
        
        # Intraday refresh (every N minutes)
        schedule.every(self.config.INTRADAY_REFRESH_INTERVAL).minutes.do(self.intraday_refresh)
        
        # End-of-day summary (3:30 PM IST)
        schedule.every().day.at(self.config.EOD_SUMMARY_TIME).do(self.end_of_day_summary)
        
        # Weekly review (Sunday)
        schedule.every().sunday.do(self.weekly_review)
        
        print("✅ Schedule configured:")
        print(f"   • Pre-market scan: {self.config.PRE_MARKET_SCAN_TIME}")
        print(f"   • Intraday refresh: Every {self.config.INTRADAY_REFRESH_INTERVAL} minutes")
        print(f"   • End-of-day summary: {self.config.EOD_SUMMARY_TIME}")
        print(f"   • Weekly review: {self.config.WEEKLY_REVIEW_DAY.capitalize()}")
    
    def run(self):
        """Run scheduler in background thread"""
        self.running = True
        self.setup_schedule()
        
        print("🚀 Automation scheduler started")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n⏹️  Automation scheduler stopped")
            self.running = False
    
    def start(self):
        """Start scheduler in background thread"""
        if self.running:
            print("⚠️  Scheduler already running")
            return
        
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("✅ Automation scheduler started in background")
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        schedule.clear()
        print("⏹️  Automation scheduler stopped")
    
    def status(self):
        """Show scheduler status"""
        print("📅 Automation Scheduler Status")
        print("=" * 70)
        print(f"Running: {self.running}")
        print(f"Enabled: {self.config.AUTOMATION_ENABLED}")
        print("")
        print("Scheduled Jobs:")
        for job in schedule.jobs:
            print(f"   • {job}")
        print("")

