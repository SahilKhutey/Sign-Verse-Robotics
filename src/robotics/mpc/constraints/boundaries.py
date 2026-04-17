import numpy as np
from typing import List

class SafetyGuardrail:
    """
    Ensures optimized ZMP targets remain within the physical support polygon.
    """
    def __init__(self, footprint_width: float = 0.4, footprint_depth: float = 0.3):
        self.max_x = footprint_width / 2.0
        self.max_y = footprint_depth / 2.0

    def clamp(self, zmp_target: float) -> float:
        """Clamps the predicted ZMP to reachable boundaries."""
        return max(-self.max_x, min(self.max_x, zmp_target))

class TrajectoryRef:
    """
    Generates reference CoM trajectories for the MPC solver.
    """
    def get_constant_ref(self, target_pos: float, horizon: int) -> List[float]:
        return [target_pos] * horizon

    def get_velocity_ref(self, current_pos: float, velocity: float, dt: float, horizon: int) -> List[float]:
        """Predicts a linear future path based on current momentum."""
        return [current_pos + velocity * dt * i for i in range(horizon)]
