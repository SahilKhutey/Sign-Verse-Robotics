import time
from typing import Dict, Any, Tuple
import numpy as np

class PID:
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def update(self, error: float) -> float:
        now = time.time()
        dt = max(0.001, now - self.last_time)
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        self.prev_error = error
        self.last_time = now
        return self.kp * error + self.ki * self.integral + self.kd * derivative

class BalanceController:
    """Checks ZMP vs Support Polygon (Footprints)."""
    def __init__(self, width: float = 0.4, depth: float = 0.3):
        self.polygon = {"x": [-width/2, width/2], "y": [-depth/2, depth/2]}

    def check_stability(self, zmp: np.ndarray) -> float:
        """Returns 0.0 (safe) to 1.0 (critically unstable)."""
        x, y = zmp[0], zmp[1]
        dist_x = abs(x) / (self.polygon["x"][1])
        dist_y = abs(y) / (self.polygon["y"][1])
        return min(1.0, max(dist_x, dist_y))

class WBCSolver:
    """
    Generates joint corrections to restore balance.
    Logic: Recover First (High Alpha) -> Blend Social (Low Alpha).
    """
    def __init__(self):
        self.pid_x = PID(kp=0.5, ki=0.1, kd=0.05)
        self.pid_y = PID(kp=0.5, ki=0.1, kd=0.05)

    def solve(self, zmp: np.ndarray, target_zmp: np.ndarray = np.array([0, 0])) -> Tuple[float, float]:
        error_x = target_zmp[0] - zmp[0]
        error_y = target_zmp[1] - zmp[1]
        
        corr_x = self.pid_x.update(error_x)
        corr_y = self.pid_y.update(error_y)
        
        return corr_x, corr_y
