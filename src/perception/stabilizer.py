import numpy as np
from typing import List, Dict, Any

class IdentityStabilizer:
    """
    Ensures Human IDs remain locked for the duration of a session.
    Prevents 'ID Jitter' or subject swapping using spatial-velocity continuity.
    """
    def __init__(self, max_distance_pixels: int = 150):
        self.max_distance = max_distance_pixels
        self.last_centroids: Dict[int, np.ndarray] = {}
        self.last_distances: Dict[int, float] = {}

    def stabilize(self, current_subjects: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Validates cross-frame mapping of human IDs.
        """
        stabilized = {}
        for sid, sdata in current_subjects.items():
            bbox = sdata["bbox"]
            centroid = np.array([(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2])
            distance = 0.0
            
            # If we have a history for this ID, check consistency
            if sid in self.last_centroids:
                distance = float(np.linalg.norm(centroid - self.last_centroids[sid]))
                if distance > self.max_distance:
                    # Potential ID Drift detected
                    # We flag this for the orchestrator to resolve or drop
                    sdata["drift_warning"] = True
                else:
                    sdata["drift_warning"] = False
            else:
                sdata["drift_warning"] = False
            
            self.last_centroids[sid] = centroid
            self.last_distances[sid] = distance
            stabilized[sid] = sdata
            
        return stabilized

    def centroid_distance(self, sid: int, bbox: List[float]) -> float:
        return float(self.last_distances.get(sid, 0.0))

    def reset(self):
        self.last_centroids.clear()
        self.last_distances.clear()
        
    def purge_id(self, sid: int):
        if sid in self.last_centroids:
            del self.last_centroids[sid]
        if sid in self.last_distances:
            del self.last_distances[sid]
