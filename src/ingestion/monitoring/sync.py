from typing import Dict, List
import numpy as np

class StreamSyncTester:
    """
    Ensures temporal alignment across multiple asynchronous motion streams.
    Detects "drift" where one source (e.g. YouTube) is lagging behind another (e.g. camera).
    """
    def __init__(self, buffer_size: int = 50):
        # source_id -> list of transition timestamps
        self.buffers: Dict[str, List[float]] = {}
        self.buffer_size = buffer_size

    def register_packet(self, source_id: str, timestamp: float):
        """
        Record the arrival/event timestamp of a packet.
        """
        if source_id not in self.buffers:
            self.buffers[source_id] = []
        
        self.buffers[source_id].append(timestamp)
        
        # Maintain window size
        if len(self.buffers[source_id]) > self.buffer_size:
            self.buffers[source_id].pop(0)

    def compute_drift(self) -> float:
        """
        Calculates the maximum temporal distance between the latest frames 
        of all active streams.
        """
        latest_times = [
            buf[-1] for buf in self.buffers.values()
            if len(buf) > 0
        ]

        if len(latest_times) < 2:
            return 0.0

        # Max drift = difference between the most ahead and most behind stream
        return max(latest_times) - min(latest_times)

    def is_synchronized(self, tolerance_ms: float = 100.0) -> bool:
        """
        Returns True if total drift is within acceptable bounds.
        """
        return (self.compute_drift() * 1000.0) <= tolerance_ms
