from collections import deque
from typing import Dict

class TemporalFilter:
    """
    Stabilizes intent decoding by applying a majority vote over a temporal window.
    Prevents high-frequency switching between contradictory intents.
    """
    def __init__(self, window_size: int = 7):
        # Per-Subject sliding buffers
        self.buffers: Dict[int, deque] = {}
        self.window_size = window_size

    def smooth(self, subject_id: int, intent: str) -> str:
        """
        Returns the dominant intent in the recent history for the subject.
        """
        if subject_id not in self.buffers:
            self.buffers[subject_id] = deque(maxlen=self.window_size)
            
        buffer = self.buffers[subject_id]
        buffer.append(intent)
        
        # Calculate Majority
        counts: Dict[str, int] = {}
        for item in buffer:
            counts[item] = counts.get(item, 0) + 1
            
        # Return the most frequent intent
        return max(counts, key=counts.get)

    def clear(self, subject_id: int):
        if subject_id in self.buffers:
            del self.buffers[subject_id]
