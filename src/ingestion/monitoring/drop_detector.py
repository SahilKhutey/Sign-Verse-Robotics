from typing import Dict

class FrameDropMonitor:
    """
    Detects skipped frames and pipeline lag spikes by tracking monotonic indices.
    """
    def __init__(self):
        self.last_index: Dict[str, int] = {}
        self.total_dropped: Dict[str, int] = {}

    def check(self, source_id: str, frame_index: int) -> int:
        """
        Calculates the number of frames dropped since the last check.
        """
        if source_id not in self.last_index:
            self.last_index[source_id] = frame_index
            self.total_dropped[source_id] = 0
            return 0

        # Frames are expected to be sequential (0, 1, 2...)
        expected = self.last_index[source_id] + 1
        dropped_count = max(0, frame_index - expected)

        if dropped_count > 0:
            self.total_dropped[source_id] += dropped_count

        self.last_index[source_id] = frame_index
        return dropped_count

    def get_stats(self, source_id: str) -> Dict[str, int]:
        return {
            "last_index": self.last_index.get(source_id, 0),
            "dropped": self.total_dropped.get(source_id, 0)
        }
