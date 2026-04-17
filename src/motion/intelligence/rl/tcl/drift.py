from collections import deque
from typing import List

class DriftDetector:
    """
    Detects long-term behavioral/social 'drift' in robot interactions.
    Flags slow degradation of engagement that short-term monitors miss.
    """
    def __init__(self, horizon: int = 500):
        self.engagement_trend = deque(maxlen=horizon)
        self.sensitivity = -0.15 # 15% drop across the horizon

    def update(self, engagement: float):
        self.engagement_trend.append(engagement)

    def detect(self) -> bool:
        """
        Analyzes the trend slope across the long horizon.
        """
        if len(self.engagement_trend) < 100:
            return False
            
        # Compare first 50 vs last 50 samples
        early_data = list(self.engagement_trend)[:50]
        recent_data = list(self.engagement_trend)[-50:]
        
        early_avg = sum(early_data) / 50
        recent_avg = sum(recent_data) / 50
        
        trend = recent_avg - early_avg
        
        if trend < self.sensitivity:
            print(f"⚠️ TCL DRIFT WARNING: Slow engagement drop detected ({trend:.2f}). Policy may be degrading.")
            return True
            
        return False
