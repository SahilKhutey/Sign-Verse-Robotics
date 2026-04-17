import numpy as np
from typing import Dict, List, Tuple

class ContactState:
    """
    Manages the physical contact phases (Static/Dynamic).
    Phases: DOUBLE, LEFT_STANCE, RIGHT_STANCE, FLIGHT (Dynamic).
    """
    def __init__(self):
        self.state = "DOUBLE"
        self.contacts = {"left_foot": True, "right_foot": True}

    def set_phase(self, phase: str):
        self.state = phase
        if phase == "LEFT_STANCE":
            self.contacts = {"left_foot": True, "right_foot": False}
        elif phase == "RIGHT_STANCE":
            self.contacts = {"left_foot": False, "right_foot": True}
        elif phase == "FLIGHT": # Dynamic only
            self.contacts = {"left_foot": False, "right_foot": False}
        else: # DOUBLE
            self.contacts = {"left_foot": True, "right_foot": True}
        return self.contacts

class ContactPlanner:
    """
    Predictive Footstep Planner for Locomotion.
    Generates target foot positions for static and dynamic gait.
    """
    def __init__(self, step_length: float = 0.25, step_width: float = 0.15):
        self.step_length = step_length
        self.step_width = step_width

    def plan_next_step(self, current_com: np.ndarray, direction: np.ndarray, phase: str) -> np.ndarray:
        """
        Plans the absolute [x, y, z] target for the swing foot.
        """
        # Linear projection of next foot target
        displacement = direction * self.step_length
        
        # Add lateral offset based on which foot is stepping
        lateral_offset = self.step_width if phase == "RIGHT_STANCE" else -self.step_width
        
        target = current_com + displacement
        target[1] += lateral_offset
        target[2] = 0.0 # Ground plane
        
        return target
