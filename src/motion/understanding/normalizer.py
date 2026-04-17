import numpy as np
from typing import Optional

class KinematicNormalizer:
    """
    Translates raw perception coordinates into a robocentric-normalized space.
    Centers the body at the torso and scales it by anatomical height.
    """
    def normalize(self, joints: np.ndarray) -> np.ndarray:
        """
        Processes (N, 3) joints into a centered, scaled coordinate space.
        """
        if joints.size == 0:
            return joints

        # 1. Centering at the root (Pelvis area)
        # MediaPipe Pose joint 0 is the nose, but 11/12 are shoulders.
        # We'll use the mean of the upper body/torso joints as a stable root
        # MediaPipe Indices: 11(L shoulder), 12(R shoulder), 23(L hip), 24(R hip)
        # Assume our fused joint vector follows consistent indices
        torso_indices = [11, 12, 23, 24] # Standard MediaPipe-aligned indices
        
        # Calculate centering root
        root = np.mean(joints[torso_indices], axis=0)
        
        # Subtract root to center at zero
        centered = joints - root
        
        # 2. Scaling Normalization (Body Size invariance)
        # We scale based on the 'Torso Height' (average of shoulders to average of hips)
        shoulder_mean = np.mean(joints[11:13], axis=0) # [11, 12]
        hip_mean = np.mean(joints[23:25], axis=0)      # [23, 24]
        
        torso_height = np.linalg.norm(shoulder_mean - hip_mean) + 1e-6
        
        # Normalize the entire cloud by this unit height
        normalized = centered / torso_height
        
        return normalized
