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

    def numerical_refinement(self, target: np.ndarray, current_angles: np.ndarray, l1: float = 0.35, l2: float = 0.35) -> np.ndarray:
        """
        Jacobian-based numerical refinement (Damped Least Squares) to avoid singularities.
        current_angles: [yaw, pitch, elbow] in radians.
        """
        angles = current_angles.copy()
        max_iters = 10
        epsilon = 1e-3
        damping = 0.01

        for _ in range(max_iters):
            # Forward Kinematics for current angles
            yaw, pitch, elbow = angles
            
            # Simple planar projection logic for quick FK
            x = (l1 * np.sin(pitch) + l2 * np.sin(pitch + elbow)) * np.sin(yaw)
            y = l1 * np.cos(pitch) + l2 * np.cos(pitch + elbow)
            z = (l1 * np.sin(pitch) + l2 * np.sin(pitch + elbow)) * np.cos(yaw)
            
            current_pos = np.array([x, y, z])
            error = target - current_pos
            
            if np.linalg.norm(error) < epsilon:
                break
                
            # Compute Analytical Jacobian (3x3)
            J = np.zeros((3, 3))
            
            # d/dyaw
            J[0, 0] = (l1 * np.sin(pitch) + l2 * np.sin(pitch + elbow)) * np.cos(yaw)
            J[1, 0] = 0.0
            J[2, 0] = -(l1 * np.sin(pitch) + l2 * np.sin(pitch + elbow)) * np.sin(yaw)
            
            # d/dpitch
            J[0, 1] = (l1 * np.cos(pitch) + l2 * np.cos(pitch + elbow)) * np.sin(yaw)
            J[1, 1] = -l1 * np.sin(pitch) - l2 * np.sin(pitch + elbow)
            J[2, 1] = (l1 * np.cos(pitch) + l2 * np.cos(pitch + elbow)) * np.cos(yaw)
            
            # d/delbow
            J[0, 2] = l2 * np.cos(pitch + elbow) * np.sin(yaw)
            J[1, 2] = -l2 * np.sin(pitch + elbow)
            J[2, 2] = l2 * np.cos(pitch + elbow) * np.cos(yaw)
            
            # Damped Least Squares: \Delta \theta = J^T (J J^T + \lambda^2 I)^{-1} \Delta x
            J_T = J.T
            JJ_T = J @ J_T
            JJ_T_damped = JJ_T + (damping ** 2) * np.eye(3)
            
            try:
                delta_theta = J_T @ np.linalg.solve(JJ_T_damped, error)
            except np.linalg.LinAlgError:
                break # Singular matrix
                
            angles += delta_theta
            
        return angles
