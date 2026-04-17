import numpy as np
from typing import Dict, Any

class MotionRefiner:
    """
    Suppresses spikes and outliers in the fused landmark signal.
    Uses median-deviation analysis to identify and clamp artifacts.
    """
    def __init__(self, deviation_threshold: float = 0.4):
        self.deviation_threshold = deviation_threshold

    def refine(self, joints: np.ndarray) -> np.ndarray:
        """
        Refines a single frame's joint landmarks using outlier suppression.
        """
        # Spatiial outlier suppression: 
        # Points that deviate significantly from the group median (relative)
        # Note: Center median is per landmark set
        median = np.median(joints, axis=0) # Per-axis median [x, y, z]
        
        # Calculate deviation per joint point
        # (N, 3) - (3,) = (N, 3)
        deviations = np.abs(joints - median)
        
        # Mask points that are too far from the typical body space
        # (Could refine with specific anatomical masks later)
        mask = np.any(deviations > self.deviation_threshold, axis=1)
        
        refined = joints.copy()
        # For outliers, we clamp them to the median position to prevent spikes
        for i in range(len(joints)):
            if mask[i]:
                refined[i] = median
                
        return refined
