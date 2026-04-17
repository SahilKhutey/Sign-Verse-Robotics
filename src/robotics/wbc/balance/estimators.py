import numpy as np
from typing import List, Dict, Any

class COMEstimator:
    """
    Center of Mass (CoM) Estimator for Humanoid Dynamics.
    Default Profile: 75kg Humanoid Surrogate.
    """
    def __init__(self):
        # Default mass distribution (kg)
        self.masses = {
            "torso": 35.0,
            "left_thigh": 10.0, "right_thigh": 10.0,
            "left_shin": 5.0, "right_shin": 5.0,
            "left_arm": 5.0, "right_arm": 5.0
        }

    def compute(self, joint_positions: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Calculates the aggregate 3D CoM position.
        joint_positions: Dict mapping link names to 3D coords [x, y, z]
        """
        total_mass = sum(self.masses.values())
        com = np.zeros(3)
        
        for link, m in self.masses.items():
            pos = joint_positions.get(link, np.array([0, 0, 0]))
            com += pos * m
            
        return com / total_mass

class ZMPEstimator:
    """
    Zero Moment Point (ZMP) Estimator.
    Determines if the robot's dynamic center is inside the support polygon.
    """
    def compute(self, com: np.ndarray, acceleration: np.ndarray, g: float = 9.81) -> np.ndarray:
        """
        com: [x, y, z] center of mass
        acceleration: [ax, ay, az] current CoM acceleration
        """
        x, y, z = com
        ax, ay, az = acceleration
        
        # ZMP planar approximation
        zmp_x = x - (z / g) * ax
        zmp_y = y - (z / g) * ay
        
        return np.array([zmp_x, zmp_y])
