from typing import List
from src.motion.intelligence.learning.experience import InteractionExperience

class TemporalCredit:
    """
    Propagates rewards backward through the interaction history.
    Ensures that actions are credited for delayed human responses (e.g., a smile after a wave).
    """
    def __init__(self, decay_factor: float = 0.8, lookback_window: int = 15):
        self.decay_factor = decay_factor
        self.lookback = lookback_window

    def assign(self, history: List[InteractionExperience], terminal_reward: float):
        """
        Updates the reward field of past experiences using a temporal decay.
        """
        if not history:
            return history
            
        # We look back from the most recent frame
        # reward(t-1) += gamma * reward(t)
        current_reward = terminal_reward
        
        # We iterate backwards through the history up to the lookback limits
        max_idx = len(history) - 1
        for i in range(max_idx, max(-1, max_idx - self.lookback), -1):
            history[i].reward += current_reward
            current_reward *= self.decay_factor
            
        return history
