import numpy as np

class LIPMModel:
    """
    Linear Inverted Pendulum Model (LIPM).
    The fundamental predictive physics model for humanoid balance.
    x_next = Ax + Bu
    """
    def __init__(self, z_com: float = 0.8, g: float = 9.81):
        self.z_com = z_com
        self.g = g
        # Eigenvalue of LIPM: omega = sqrt(g/z)
        self.omega = np.sqrt(self.g / self.z_com)

    def step(self, state: np.ndarray, zmp_input: float, dt: float) -> np.ndarray:
        """
        state: [pos, vel]
        zmp_input: u (Target ZMP)
        dt: Time step
        Returns: [pos_next, vel_next]
        """
        x, dx = state
        u = zmp_input
        
        # ddx = (g/z) * (x - u)
        ddx = (self.omega**2) * (x - u)
        
        dx_next = dx + ddx * dt
        x_next = x + dx * dt
        
        return np.array([x_next, dx_next])
