from typing import List, Deque
from collections import deque

class RewardStabilizer:
    """
    Filters per-frame reward noise to ensure stable behavioral learning.
    Uses a moving average to smooth lighting/occlusion glitches.
    """
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.history: Deque[float] = deque(maxlen=window_size)

    def smooth(self, raw_reward: float) -> float:
        """
        Returns a smoothed reward based on recent history.
        """
        self.history.append(raw_reward)
        if not self.history:
            return 0.0
        return sum(self.history) / len(self.history)

    def reset(self):
        self.history.clear()
