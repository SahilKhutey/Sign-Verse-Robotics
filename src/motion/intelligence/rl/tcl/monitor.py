from typing import List, Dict, Any
from collections import deque

class HealthMonitor:
    """
    Multivariate Health Monitoring for Sign-Verse Intelligence.
    Analyzes social alignment, behavioral diversity, and perception stability.
    """
    def __init__(self, history_len: int = 200):
        self.engagement_history = deque(maxlen=history_len)
        self.stability_history = deque(maxlen=history_len)
        self.action_history = deque(maxlen=history_len)
        self.threshold = 0.35

    def track(self, engagement: float, stability: float, action_idx: int):
        self.engagement_history.append(engagement)
        self.stability_history.append(stability)
        self.action_history.append(action_idx)

    def evaluate(self) -> float:
        """
        Calculates a unified health score [0.0 - 1.0].
        """
        if not self.engagement_history:
            return 1.0
            
        # 1. Social Engagement (Weight: 0.5)
        avg_eng = sum(self.engagement_history) / len(self.engagement_history)
        
        # 2. Perception Stability (Weight: 0.3)
        avg_stab = sum(self.stability_history) / len(self.stability_history)
        
        # 3. Behavioral Diversity (Weight: 0.2)
        # Penalize if only one action is being performed (spamming)
        unique_actions = len(set(self.action_history))
        diversity = min(1.0, unique_actions / 4.0)
        
        score = (avg_eng * 0.5) + (avg_stab * 0.3) + (diversity * 0.2)
        return float(score)

    def should_rollback(self) -> bool:
        """Triggers rollback if the multi-metric score fails."""
        if len(self.engagement_history) < 100: # Warm up
            return False
        return self.evaluate() < self.threshold
