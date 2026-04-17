import numpy as np
from typing import List, Dict, Any
from src.robotics.mpc.model.dynamics import LIPMModel

class MPCSolver:
    """
    Predictive Optimizer for Humanoid Balance.
    Horizon: 20 steps (1.0s @ 20Hz).
    Computes optimal ZMP target to minimize future CoM deviation.
    """
    def __init__(self, model: LIPMModel, horizon: int = 20, dt: float = 0.05):
        self.model = model
        self.horizon = horizon
        self.dt = dt

    def optimize(self, current_state: np.ndarray, ref_trajectory: List[float]) -> float:
        """
        Input: [pos, vel] CoM state, 20-step target CoM positions.
        Output: Optimal ZMP input 'u' for the current frame.
        """
        best_u = 0.0
        min_cost = float('inf')
        
        # Predictive Search over candidate ZMP inputs
        # (In production, replace with a Quadratic Program solver like OSQP)
        candidates = np.linspace(-0.25, 0.25, 21) # Search within +/- 25cm
        
        for u in candidates:
            cost = 0.0
            temp_state = current_state.copy()
            
            # Simulate the 20-step look-ahead
            for t in range(self.horizon):
                temp_state = self.model.step(temp_state, u, self.dt)
                
                # Cost function: State Deviation + Control Effort
                ref = ref_trajectory[t] if t < len(ref_trajectory) else ref_trajectory[-1]
                pos_error = (temp_state[0] - ref)**2
                effort_cost = 0.1 * (u**2) # Penalize aggressive ZMP offsets
                
                cost += pos_error + effort_cost
                
            if cost < min_cost:
                min_cost = cost
                best_u = u
                
        return best_u
