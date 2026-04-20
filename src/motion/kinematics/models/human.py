import numpy as np
from typing import Dict, List, Tuple

class HumanSkeleton:
    """
    Geometric utility for extracting 3D vectors and joint angles from human landmarks.
    This serves as the 'Observation Layer' for universal kinematic mapping.
    """
    def __init__(self, joints: np.ndarray):
        """
        :param joints: (N, 3) array of joint coordinates (x, y, z).
        """
        self.joints = joints

    def get_vector(self, start_idx: int, end_idx: int) -> np.ndarray:
        """Computes a 3D vector between two joints."""
        if start_idx >= len(self.joints) or end_idx >= len(self.joints):
            return np.zeros(3)
        return self.joints[end_idx] - self.joints[start_idx]

    def get_angle(self, idx_a: int, idx_b: int, idx_c: int) -> float:
        """
        Computes the 3D angle at joint 'b' between joints 'a' and 'c'.
        Returns value in radians.
        """
        v1 = self.get_vector(idx_b, idx_a)
        v2 = self.get_vector(idx_b, idx_c)

        # Normalize vectors
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0

        v1_u = v1 / norm1
        v2_u = v2 / norm2

        # Use dot product to find angle
        cos_theta = np.dot(v1_u, v2_u)
        angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))
        
        return angle

    def get_plane_angle(self, idx_a: int, idx_b: int, idx_c: int, plane: str = 'xy') -> float:
        """
        Computes the 2D angle in a specific planar projection.
        Useful for DOF-limited joints (e.g. elbow hinge).
        """
        p_map = {'xy': [0, 1], 'xz': [0, 2], 'yz': [1, 2]}
        dims = p_map.get(plane, [0, 1])
        
        v1 = self.get_vector(idx_b, idx_a)[dims]
        v2 = self.get_vector(idx_b, idx_c)[dims]
        
        angle = np.arctan2(v2[1], v2[0]) - np.arctan2(v1[1], v1[0])
        return angle
