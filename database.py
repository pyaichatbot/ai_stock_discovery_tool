"""
AI-Powered Stock Discovery Tool - Database Layer
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import json


class PickLedger:
    """SQLite-based storage for picks, feedback, outcomes, and learning"""
    
    def __init__(self, db_path: str = "picks_ledger.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create tables if not exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Picks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pick_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                conviction_score REAL,
                risk_score REAL,
                entry_price REAL,
                stop_loss REAL,
                target_price REAL,
                position_size REAL,
                market_regime TEXT,
                features_json TEXT,
                trade_plan_json TEXT
            )
        """)
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pick_id TEXT NOT NULL,
                took_trade INTEGER,
                rating INTEGER,
                notes TEXT,
                rejection_reason TEXT,
                timestamp TEXT,
                FOREIGN KEY (pick_id) REFERENCES picks(pick_id)
            )
        """)
        
        # Outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pick_id TEXT NOT NULL,
                mfe REAL,
                mae REAL,
                final_return REAL,
                hit_target INTEGER,
                hit_stop INTEGER,
                outcome_timestamp TEXT,
                FOREIGN KEY (pick_id) REFERENCES picks(pick_id)
            )
        """)
        
        # Strategy performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                regime TEXT NOT NULL,
                total_picks INTEGER DEFAULT 0,
                successful_picks INTEGER DEFAULT 0,
                avg_return REAL DEFAULT 0.0,
                weight REAL DEFAULT 1.0,
                last_updated TEXT,
                UNIQUE(strategy, regime)
            )
        """)
        
        # Feature penalties table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_penalties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT NOT NULL,
                feature_value TEXT NOT NULL,
                penalty_score REAL DEFAULT 0.0,
                occurrences INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                last_updated TEXT,
                UNIQUE(feature_name, feature_value)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_pick(self, pick: Dict) -> str:
        """Store a generated pick"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert features to JSON-serializable format (convert bools to ints)
        features = pick.get('features', {})
        features_serializable = self._make_json_serializable(features)
        
        cursor.execute("""
            INSERT INTO picks (
                pick_id, symbol, strategy, timestamp, conviction_score,
                risk_score, entry_price, stop_loss, target_price,
                position_size, market_regime, features_json, trade_plan_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pick['pick_id'], pick['symbol'], pick['strategy'],
            pick['timestamp'], pick['conviction_score'], pick['risk_score'],
            pick['entry_price'], pick['stop_loss'], pick['target_price'],
            pick['position_size'], pick.get('market_regime', 'unknown'),
            json.dumps(features_serializable),
            json.dumps(pick.get('trade_plan', {}))
        ))
        
        conn.commit()
        conn.close()
        return pick['pick_id']
    
    def _make_json_serializable(self, obj):
        """Recursively convert objects to JSON-serializable format"""
        if isinstance(obj, bool):
            return 1 if obj else 0
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str)) or obj is None:
            return obj
        else:
            return str(obj)  # Fallback: convert to string
    
    def add_feedback(self, pick_id: str, took: bool, rating: int, 
                     notes: str = "", rejection_reason: str = ""):
        """Record user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (pick_id, took_trade, rating, notes, rejection_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pick_id, 1 if took else 0, rating, notes, rejection_reason, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def save_outcome(self, pick_id: str, mfe: float, mae: float, 
                     final_return: float, hit_target: bool, hit_stop: bool):
        """Store realized outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO outcomes (pick_id, mfe, mae, final_return, hit_target, hit_stop, outcome_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pick_id, mfe, mae, final_return, 1 if hit_target else 0, 
              1 if hit_stop else 0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_strategy_performance(self, strategy: str, regime: str) -> Optional[Dict]:
        """Get performance stats for a strategy in a given regime"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT total_picks, successful_picks, avg_return, weight
            FROM strategy_stats
            WHERE strategy = ? AND regime = ?
        """, (strategy, regime))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'total_picks': result[0],
                'successful_picks': result[1],
                'avg_return': result[2],
                'weight': result[3]
            }
        return None
    
    def update_strategy_performance(self, strategy: str, regime: str, 
                                    successful: bool, return_pct: float):
        """Update strategy performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute("""
            SELECT total_picks, successful_picks, avg_return
            FROM strategy_stats
            WHERE strategy = ? AND regime = ?
        """, (strategy, regime))
        
        result = cursor.fetchone()
        
        if result:
            total = result[0] + 1
            successful_count = result[1] + (1 if successful else 0)
            # Running average
            new_avg = ((result[2] * result[0]) + return_pct) / total
            
            cursor.execute("""
                UPDATE strategy_stats
                SET total_picks = ?, successful_picks = ?, avg_return = ?, last_updated = ?
                WHERE strategy = ? AND regime = ?
            """, (total, successful_count, new_avg, datetime.now().isoformat(), strategy, regime))
        else:
            # First entry for this strategy/regime
            cursor.execute("""
                INSERT INTO strategy_stats (strategy, regime, total_picks, successful_picks, avg_return, weight, last_updated)
                VALUES (?, ?, 1, ?, ?, 1.0, ?)
            """, (strategy, regime, 1 if successful else 0, return_pct, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_total_picks_count(self) -> int:
        """Get total number of picks generated"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM picks")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_feature_penalty(self, feature_name: str, feature_value: str) -> float:
        """Get penalty score for a feature pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT penalty_score FROM feature_penalties
            WHERE feature_name = ? AND feature_value = ?
        """, (feature_name, feature_value))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
    
    def update_feature_penalty(self, feature_name: str, feature_value: str, failed: bool):
        """Update feature penalty based on outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT occurrences, failures FROM feature_penalties
            WHERE feature_name = ? AND feature_value = ?
        """, (feature_name, feature_value))
        
        result = cursor.fetchone()
        
        if result:
            new_occurrences = result[0] + 1
            new_failures = result[1] + (1 if failed else 0)
            failure_rate = new_failures / new_occurrences
            
            # Penalty increases with failure rate
            penalty = min(30.0, failure_rate * 50.0)  # Max 30 point penalty
            
            cursor.execute("""
                UPDATE feature_penalties
                SET occurrences = ?, failures = ?, penalty_score = ?, last_updated = ?
                WHERE feature_name = ? AND feature_value = ?
            """, (new_occurrences, new_failures, penalty, datetime.now().isoformat(), 
                  feature_name, feature_value))
        else:
            cursor.execute("""
                INSERT INTO feature_penalties (feature_name, feature_value, occurrences, failures, penalty_score, last_updated)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (feature_name, feature_value, 1 if failed else 0, 
                  10.0 if failed else 0.0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_picks_without_outcomes(self) -> List[Dict]:
        """Get picks that don't have outcomes yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.pick_id, p.symbol, p.strategy, p.entry_price, p.stop_loss, p.target_price, p.timestamp
            FROM picks p
            LEFT JOIN outcomes o ON p.pick_id = o.pick_id
            WHERE o.pick_id IS NULL
            ORDER BY p.timestamp DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        picks = []
        for row in results:
            picks.append({
                'pick_id': row[0],
                'symbol': row[1],
                'strategy': row[2],
                'entry_price': row[3],
                'stop_loss': row[4],
                'target_price': row[5],
                'timestamp': row[6]
            })
        
        return picks
    
    def get_pick_details(self, pick_id: str) -> Optional[Dict]:
        """Get pick details by pick_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strategy, market_regime, features_json, conviction_score
            FROM picks WHERE pick_id = ?
        """, (pick_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'strategy': result[0],
            'market_regime': result[1],
            'features_json': result[2],
            'conviction_score': result[3]
        }