import numpy as np
from typing import Optional

class JointSmoother:
    """
    Temporal joint stabilization using Exponential Moving Average (EMA).
    Reduces skeletal jitter in high-frequency human motion capture.
    """
    def __init__(self, alpha: float = 0.7):
        """
        :param alpha: Smoothing factor [0, 1]. 
                      1.0 = no smoothing (raw detection).
                      0.5 = heavy smoothing (reduced jitter, higher latency).
        """
        self.alpha = alpha
        self.prev_joints: Optional[np.ndarray] = None

    def smooth(self, current_joints: np.ndarray) -> np.ndarray:
        """
        Applies EMA to the incoming joint array.
        Expected current_joints shape: (N, 3)
        """
        if self.prev_joints is None:
            self.prev_joints = current_joints
            return current_joints

        # Ensure shapes match (handle multi-person/dynamic skeleton)
        if current_joints.shape != self.prev_joints.shape:
            self.prev_joints = current_joints
            return current_joints

        smoothed = self.alpha * current_joints + (1 - self.alpha) * self.prev_joints
        self.prev_joints = smoothed
        return smoothed

    def reset(self):
        self.prev_joints = None
