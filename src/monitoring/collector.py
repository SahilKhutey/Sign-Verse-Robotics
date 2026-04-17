import time
from collections import defaultdict, deque
from typing import Dict, Any

class MetricsCollector:
    """
    Production-grade Metrics Aggregator for Sign-Verse Robotics.
    Tracks sub-second FPS, rolling latency, and frame drops per source.
    """
    def __init__(self, window_size: int = 100):
        self.fps_counter = defaultdict(int)
        self.last_time = defaultdict(lambda: time.time())
        
        # source_id -> rolling window of values
        self.latency_buffer = defaultdict(lambda: deque(maxlen=window_size))
        self.drop_buffer = defaultdict(int)
        self.frame_count = defaultdict(int)
        self.current_intent = "IDLE"
        self.intent_confidence = 0.0
        self.subject_count = 0

    def record_frame(self, source_id: str):
        """Signals that a frame has been ingested."""
        self.fps_counter[source_id] += 1
        self.frame_count[source_id] += 1

    def record_latency(self, source_id: str, latency: float):
        """Records end-to-end latency in seconds."""
        self.latency_buffer[source_id].append(latency)

    def record_drops(self, source_id: str, count: int):
        """Records detected frame drops."""
        self.drop_buffer[source_id] += count

    def record_intent(self, intent: str, confidence: float):
        """Captures decoded human intent for telemetry."""
        self.current_intent = intent
        self.intent_confidence = confidence

    def compute_fps(self, source_id: str) -> float:
        """Calculates current FPS based on the elapsed time since the last window."""
        now = time.time()
        elapsed = now - self.last_time[source_id]
        
        if elapsed < 0.1: # Threshold to avoid jitter on low samples
            return 0.0

        fps = self.fps_counter[source_id] / elapsed
        
        # Reset counter for next window
        self.fps_counter[source_id] = 0
        self.last_time[source_id] = now
        
        return round(fps, 2)

    def get_avg_latency(self, source_id: str) -> float:
        """Returns average latency in milliseconds."""
        buf = self.latency_buffer[source_id]
        if not buf:
            return 0.0
        return round((sum(buf) / len(buf)) * 1000.0, 2)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Returns a complete snapshot of the system metrics for the dashboard."""
        stats = {}
        for source_id in list(self.last_time.keys()):
            stats[source_id] = {
                "fps": self.compute_fps(source_id),
                "latency_ms": self.get_avg_latency(source_id),
                "total_drops": self.drop_buffer[source_id],
                "total_frames": self.frame_count[source_id],
                "current_intent": self.current_intent,
                "intent_confidence": self.intent_confidence,
                "active_subjects": self.subject_count
            }
        return stats
