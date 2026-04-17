import numpy as np

class FullBodyDynamics:
    """
    Whole-Body Predictive Physics Model.
    Models the robot as a multi-link system with contact forces.
    x_next = f(x, u, f_ext)
    """
    def __init__(self, mass: float = 75.0, g: float = 9.81):
        self.mass = mass
        self.g = g

    def step(self, state: np.ndarray, control_acc: np.ndarray, forces: np.ndarray, dt: float) -> np.ndarray:
        """
        state: [pos, vel] (Full body or CoM)
        control_acc: [ax, ay, az] derived from joint torques
        forces: [fx, fy, fz] external contact forces (GRF)
        """
        pos, vel = state[:3], state[3:]
        
        # Net acceleration: Control + External Forces / Mass - Gravity
        net_acc = control_acc + (forces / self.mass) - np.array([0, 0, self.g])
        
        vel_next = vel + net_acc * dt
        pos_next = pos + vel * dt
        
        return np.concatenate([pos_next, vel_next])
