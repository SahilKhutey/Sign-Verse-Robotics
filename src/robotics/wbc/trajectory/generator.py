import numpy as np
from typing import List, Dict, Any

class TrajectoryGenerator:
    """
    Smooths robotic joint paths to prevent jerk and hardware stress.
    Implements Linear and Sine-based smoothing.
    """
    def smooth_transition(self, start: np.ndarray, end: np.ndarray, steps: int = 15) -> List[np.ndarray]:
        trajectory = []
        for i in range(steps):
            # Sigmoid/Sine-based easing for organic motion
            alpha = (1 - np.cos(np.pi * i / (steps - 1))) / 2
            interpolated = start + (end - start) * alpha
            trajectory.append(interpolated)
        return trajectory

class GaitPlanner:
    """
    High-level bipedal walking logic for humanoid gait.
    Manages support phases: Left, Right, Double.
    """
    def __init__(self):
        self.phases = ["DOUBLE", "LEFT_SUPPORT", "DOUBLE", "RIGHT_SUPPORT"]
        self.current_idx = 0

    def next_phase(self) -> str:
        self.current_idx = (self.current_idx + 1) % len(self.phases)
        return self.phases[self.current_idx]

    def get_current_support(self) -> str:
        return self.phases[self.current_idx]
