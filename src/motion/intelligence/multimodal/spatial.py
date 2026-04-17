import numpy as np
from typing import Dict, Any

class SpatialAwarenessEngine:
    """
    Computes HRI-grade proxemics and social zones.
    Calculates distance based on the Robot's Base Origin.
    """
    def __init__(self, camera_to_base_offset: np.ndarray = np.array([0.0, -1.2, 0.0])):
        # Assuming camera is 1.2m above base in +Y
        self.offset = camera_to_base_offset

    def compute(self, position_cam: np.ndarray) -> Dict[str, Any]:
        """
        Transforms camera-space position to robot-base space and classifies zone.
        """
        # 1. Transform to Robot Origin
        # pos_robot = pos_cam + offset
        pos_robot = position_cam + self.offset
        
        # 2. Euclidean Distance from Base
        distance = np.linalg.norm(pos_robot)
        
        # 3. Social Zone Classification (Proxemics)
        if distance < 1.2:
            zone = "INTIMATE"  # Very close interaction
        elif distance < 3.5:
            zone = "SOCIAL"    # Standard engagement distance
        else:
            zone = "PUBLIC"    # Awareness but no direct interaction
            
        return {
            "distance": distance,
            "zone": zone,
            "pos_robot": pos_robot
        }
