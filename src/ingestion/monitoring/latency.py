import time
from collections import defaultdict, deque
from typing import Dict, List

class LatencyTracker:
    """
    High-resolution telemetry for measuring end-to-end ingestion latency.
    Tracks frame-by-frame delays across multiple sources.
    """
    def __init__(self, window_size: int = 100):
        # source_id -> deque of event timestamps
        self.timestamps = defaultdict(lambda: deque(maxlen=window_size))

    def mark(self, source_id: str, event_type: str):
        """
        Marks a specific event (e.g., 'ingress', 'normalized', 'pushed') 
        with a high-precision counter.
        """
        self.timestamps[source_id].append({
            "event": event_type,
            "time": time.perf_counter()
        })

    def get_latency(self, source_id: str) -> float:
        """
        Returns the total delay between the first and last recorded events 
        for the current source window.
        """
        events = list(self.timestamps[source_id])
        if len(events) < 2:
            return 0.0

        # Calculate difference between earliest and latest event in the window
        start = events[0]["time"]
        end = events[-1]["time"]

        return end - start

    def report(self) -> Dict[str, float]:
        """
        Returns a snapshot of average latencies across all active sources.
        """
        return {
            src: self.get_latency(src)
            for src in self.timestamps.keys()
        }
