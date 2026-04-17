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

    def stabilize(self, current_subjects: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Validates cross-frame mapping of human IDs.
        """
        stabilized = {}
        for sid, sdata in current_subjects.items():
            bbox = sdata["bbox"]
            centroid = np.array([(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2])
            
            # If we have a history for this ID, check consistency
            if sid in self.last_centroids:
                dist = np.linalg.norm(centroid - self.last_centroids[sid])
                if dist > self.max_distance:
                    # Potential ID Drift detected
                    # We flag this for the orchestrator to resolve or drop
                    sdata["drift_warning"] = True
            
            self.last_centroids[sid] = centroid
            stabilized[sid] = sdata
            
        return stabilized

    def reset(self):
        self.last_centroids.clear()
        
    def purge_id(self, sid: int):
        if sid in self.last_centroids:
            del self.last_centroids[sid]
