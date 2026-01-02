"""
AI-Powered Stock Discovery Tool - Learning & Adaptation Module
Phase 3: Feedback Learning Loop
"""

import numpy as np
from typing import Dict, List
from database import PickLedger
from config import Config


class LearningEngine:
    """Adaptive learning from feedback and outcomes"""
    
    def __init__(self, config: Config, ledger: PickLedger):
        self.config = config
        self.ledger = ledger
        
        # Strategy base weights (equal start)
        self.strategy_weights = {
            'ORB': 1.0,
            'VWAP_PULLBACK': 1.0,
            'MOMENTUM_SWING': 1.0,
            'HVB': 1.0
        }
    
    def should_learn(self) -> bool:
        """Determine if enough data exists to start learning"""
        total_picks = self.ledger.get_total_picks_count()
        return total_picks >= self.config.MIN_TRADES_BEFORE_LEARNING
    
    def get_learning_mode(self) -> str:
        """Determine learning aggressiveness"""
        total_picks = self.ledger.get_total_picks_count()
        
        if total_picks < self.config.MIN_TRADES_BEFORE_LEARNING:
            return "baseline"
        elif total_picks < self.config.CONSERVATIVE_LEARNING_THRESHOLD:
            return "conservative"
        else:
            return "full"
    
    def update_from_outcome(self, pick_id: str, outcome: Dict, feedback: Dict = None):
        """
        Update learning based on realized outcome
        
        Args:
            pick_id: The pick identifier
            outcome: Dict with mfe, mae, final_return, hit_target, hit_stop
            feedback: Optional user feedback dict
        """
        # Get pick details
        pick_details = self.ledger.get_pick_details(pick_id)
        
        if not pick_details:
            return
        
        strategy = pick_details['strategy']
        regime = pick_details['market_regime']
        features_json = pick_details['features_json']
        conviction = pick_details['conviction_score']
        
        # Determine success
        successful = outcome['final_return'] > 0 or outcome['hit_target']
        failed = outcome['hit_stop'] or outcome['final_return'] < -5.0
        
        # Update strategy performance
        self.ledger.update_strategy_performance(
            strategy, 
            regime, 
            successful, 
            outcome['final_return']
        )
        
        # Update feature penalties if failed
        if failed:
            import json
            features = json.loads(features_json) if features_json else {}
            
            # Check for problematic patterns
            self._update_feature_penalties(features, failed=True)
        
        # Recalculate strategy weights if in learning mode
        if self.should_learn():
            self._recalculate_weights(regime)
    
    def _update_feature_penalties(self, features: Dict, failed: bool):
        """Update penalties for feature patterns"""
        # Low liquidity + high volatility = penalty
        if 'avg_volume' in features and features.get('volatility_percentile', 0) > 90:
            if features['avg_volume'] < self.config.MIN_AVG_VOLUME * 1.5:
                self.ledger.update_feature_penalty(
                    'low_liquidity_hvb', 
                    'true', 
                    failed
                )
        
        # Large gap without volume = penalty
        if 'breakout_pct' in features and features.get('volume_surge') == False:
            if features['breakout_pct'] > 3.0:
                self.ledger.update_feature_penalty(
                    'gap_no_volume',
                    'true',
                    failed
                )
        
        # Weak structure = penalty
        if 'distance_from_vwap_pct' in features:
            if features['distance_from_vwap_pct'] > 2.0:
                self.ledger.update_feature_penalty(
                    'far_from_vwap',
                    'true',
                    failed
                )
    
    def _recalculate_weights(self, current_regime: str):
        """Recalculate strategy weights using bandit-style learning"""
        learning_mode = self.get_learning_mode()
        
        if learning_mode == "baseline":
            return  # No adjustment yet
        
        # Get performance for each strategy in current regime
        for strategy in self.strategy_weights.keys():
            perf = self.ledger.get_strategy_performance(strategy, current_regime)
            
            if perf is None or perf['total_picks'] < 5:
                continue  # Need minimum sample
            
            # Calculate expectancy
            win_rate = perf['successful_picks'] / perf['total_picks']
            avg_return = perf['avg_return']
            expectancy = win_rate * avg_return
            
            # Adjust weight based on expectancy
            if expectancy > 1.0:  # Positive expectancy
                adjustment = self.config.WEIGHT_ADJUSTMENT_CONSERVATIVE if learning_mode == "conservative" else self.config.WEIGHT_ADJUSTMENT_FULL
                self.strategy_weights[strategy] = min(1.5, self.strategy_weights[strategy] + adjustment)
            elif expectancy < -0.5:  # Negative expectancy
                adjustment = self.config.WEIGHT_ADJUSTMENT_CONSERVATIVE if learning_mode == "conservative" else self.config.WEIGHT_ADJUSTMENT_FULL
                self.strategy_weights[strategy] = max(0.5, self.strategy_weights[strategy] - adjustment)
    
    def apply_learning_to_score(self, pick: Dict, regime: str) -> Dict:
        """
        Apply learned adjustments to a pick's conviction score
        
        Returns updated pick with adjusted conviction and explanation
        """
        if not self.should_learn():
            return pick  # No adjustments in baseline mode
        
        strategy = pick['strategy']
        original_conviction = pick['conviction_score']
        adjustments = []
        
        # Apply strategy weight
        strategy_weight = self.strategy_weights.get(strategy, 1.0)
        weight_adjustment = (strategy_weight - 1.0) * 20  # ±20 points max
        
        if abs(weight_adjustment) > 1.0:
            adjustments.append(f"Strategy weight: {weight_adjustment:+.1f} ({strategy} performance in {regime})")
        
        # Apply feature penalties
        features = pick.get('features', {})
        total_penalty = 0.0
        
        # Check low liquidity HVB
        if strategy == 'HVB' and 'avg_volume' in features:
            if features['avg_volume'] < self.config.MIN_AVG_VOLUME * 1.5:
                penalty = self.ledger.get_feature_penalty('low_liquidity_hvb', 'true')
                if penalty > 0:
                    total_penalty += penalty
                    adjustments.append(f"Penalty: -{penalty:.1f} (low liquidity HVB pattern)")
        
        # Check gap without volume
        if 'breakout_pct' in features and not features.get('volume_surge', True):
            if features['breakout_pct'] > 3.0:
                penalty = self.ledger.get_feature_penalty('gap_no_volume', 'true')
                if penalty > 0:
                    total_penalty += penalty
                    adjustments.append(f"Penalty: -{penalty:.1f} (gap without volume)")
        
        # Check far from VWAP
        if 'distance_from_vwap_pct' in features:
            if features['distance_from_vwap_pct'] > 2.0:
                penalty = self.ledger.get_feature_penalty('far_from_vwap', 'true')
                if penalty > 0:
                    total_penalty += penalty
                    adjustments.append(f"Penalty: -{penalty:.1f} (far from VWAP)")
        
        # Calculate final conviction
        adjusted_conviction = original_conviction + weight_adjustment - total_penalty
        adjusted_conviction = max(0.0, min(100.0, adjusted_conviction))  # Clamp to 0-100
        
        # Update pick
        pick['conviction_score'] = adjusted_conviction
        pick['original_conviction'] = original_conviction
        pick['learning_adjustments'] = adjustments
        
        return pick
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get current strategy weights for transparency"""
        return self.strategy_weights.copy()
