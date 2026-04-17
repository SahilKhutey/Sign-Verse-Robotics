import numpy as np
from typing import Tuple, Optional

class SimpleIK:
    """
    Inverse Kinematics Solver for Universal Humanoid limbs.
    Provides analytical and numerical reachability for Target-to-Joint mapping.
    """
    def solve_arm_3d(self, target: np.ndarray, l1: float = 0.35, l2: float = 0.35) -> Tuple[float, float, float]:
        """
        Calculates 3-DOF shoulder/elbow angles for a target (x, y, z).
        :param target: (x, y, z) relative to shoulder.
        :param l1: Upper arm length (meters).
        :param l2: Forearm length (meters).
        """
        x, y, z = target
        
        # 1. Distance to target
        d = np.sqrt(x**2 + y**2 + z**2)
        
        # 2. Check reachability
        if d > (l1 + l2):
            # Target out of reach, scale to maximum extent
            scale = (l1 + l2) / d
            x, y, z = x * scale, y * scale, z * scale
            d = l1 + l2

        # 3. Shoulder Yaw
        theta_yaw = np.arctan2(x, z)

        # 4. Law of Cosines for Elbow Pitch
        cos_elbow = (d**2 - l1**2 - l2**2) / (2 * l1 * l2)
        theta_elbow = np.arccos(np.clip(cos_elbow, -1.0, 1.0))

        # 5. Shoulder Pitch
        a = l2 * np.sin(theta_elbow)
        b = l1 + l2 * np.cos(theta_elbow)
        theta_shoulder = np.arctan2(y, np.sqrt(x**2 + z**2)) + np.arctan2(a, b)

        return (
            np.degrees(theta_yaw),
            np.degrees(theta_shoulder),
            np.degrees(theta_elbow)
        )

    def numerical_refinement(self, target: np.ndarray, current_angles: np.ndarray):
        """
        Placeholder for Jacobian-based numerical refinement if analytical solution hits singularity.
        """
        pass
