import numpy as np
from typing import Dict, Any, Tuple

class EmotionStabilizer:
    """
    Prevents emotion flickering using confidence-weighted history.
    """
    def __init__(self, persistence: float = 0.8):
        self.persistence = persistence
        self.prev_state: Dict[int, Tuple[str, float]] = {} # id -> (emotion, confidence)

    def stabilize(self, subject_id: int, emotion: str, confidence: float) -> str:
        """
        Locks emotion if the new signal is low confidence.
        """
        if subject_id not in self.prev_state:
            self.prev_state[subject_id] = (emotion, confidence)
            return emotion
            
        prev_emotion, prev_conf = self.prev_state[subject_id]
        
        # If current confidence is low (e.g. head turn), persist previous emotion
        if confidence < 0.4:
            return prev_emotion
            
        # Update state
        self.prev_state[subject_id] = (emotion, confidence)
        return emotion

class EngagementTracker:
    """
    Temporally smooths engagement scores to ensure natural transitions.
    """
    def __init__(self, window: int = 10):
        self.window = window
        self.history: Dict[int, list] = {}

    def update(self, subject_id: int, score: float) -> float:
        """
        Returns a smoothed engagement score.
        """
        if subject_id not in self.history:
            self.history[subject_id] = []
            
        history = self.history[subject_id]
        history.append(score)
        
        if len(history) > self.window:
            history.pop(0)
            
        return float(np.mean(history))
