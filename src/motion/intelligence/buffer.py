from collections import deque
from typing import List
from src.motion.core.state import MotionState

class TemporalBuffer:
    """
    Thread-safe sliding window for MotionStates.
    Allows reasoning over time (e.g. past 1-2 seconds of motion).
    """
    def __init__(self, max_size: int = 60): # ~2 seconds at 30fps
        self.buffer = deque(maxlen=max_size)

    def add(self, state: MotionState):
        """Append a new state to the temporal history."""
        self.buffer.append(state)

    def get_sequence(self) -> List[MotionState]:
        """Returns the current temporal window as a list."""
        return list(self.buffer)

    def is_ready(self) -> bool:
        """Returns True if the buffer has enough data for analysis."""
        return len(self.buffer) >= (self.buffer.maxlen // 2)
