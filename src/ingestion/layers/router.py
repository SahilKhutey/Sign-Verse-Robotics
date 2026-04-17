import uuid
from typing import Dict, Any

class TemporalRouter:
    """
    Production Layer 2: Temporal Routing.
    Calculates time deltas (dt) and manages monotonic frame indexing within a session.
    """
    def __init__(self):
        self.last_timestamp: Dict[str, float] = {}
        self.sequence_index: Dict[str, int] = {}
        self.sequence_ids: Dict[str, str] = {}

    def route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        source_id = data["source_id"]

        # Initialize a new sequence if source is new
        if source_id not in self.sequence_ids:
            self.sequence_ids[source_id] = str(uuid.uuid4())
            self.sequence_index[source_id] = 0
            self.last_timestamp[source_id] = data["timestamp"]

        # Calculate time delta (dt)
        current_ts = data["timestamp"]
        dt = current_ts - self.last_timestamp[source_id]
        self.last_timestamp[source_id] = current_ts

        # Enrich data with temporal identifiers
        data.update({
            "sequence_id": self.sequence_ids[source_id],
            "sequence_index": self.sequence_index[source_id],
            "time_delta": dt
        })

        # Advance local sequence index
        self.sequence_index[source_id] += 1

        return data
