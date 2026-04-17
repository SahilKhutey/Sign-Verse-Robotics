import numpy as np
from collections import deque
from typing import Dict, Any

class TemporalSmoothing:
    """
    Applies window-based mean smoothing to joint sequences.
    Maintains a temporal buffer per subject-ID to remove high-frequency noise.
    """
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.buffers: Dict[int, deque] = {}

    def apply(self, subject_id: int, joints: np.ndarray) -> np.ndarray:
        """
        Smooths the current joint landmarks using the temporal window.
        """
        if subject_id not in self.buffers:
            self.buffers[subject_id] = deque(maxlen=self.window_size)
        
        buffer = self.buffers[subject_id]
        buffer.append(joints)
        
        if len(buffer) < 2:
            return joints
            
        # Compute the weighted mean across the window
        # (Uniform weights for simplicity, could use exponential decay)
        return np.mean(list(buffer), axis=0)

    def reset_id(self, subject_id: int):
        if subject_id in self.buffers:
            del self.buffers[subject_id]
