import numpy as np
import time
from typing import Optional, List, Dict, Any
from src.motion.core.state import MotionState
from src.motion.filters.kalman import KalmanFilter
from src.motion.skeleton.smoother import JointSmoother
from src.db.schemas import HumanSubject

class MotionFusionEngine:
    """
    Orchestrates the transition from Perception (Level 3) to Fusion (Level 4/5).
    Converts raw landmark detections into a stabilized, robocentric state.
    Now supports Multi-ID subject tracking.
    """
    def __init__(self, dt: float = 1/30.0, smoothing_alpha: float = 0.7):
        self.dt = dt
        self.alpha = smoothing_alpha
        
        # Multi-ID state buffers
        self.states: Dict[int, Dict[str, Any]] = {} 

    def process_refined_joints(self, subject_id: int, joints: np.ndarray, confidence: float, source_id: str, timestamp: float) -> MotionState:
        """
        Processes pre-fused and normalized joints through temporal stabilization.
        """
        sid = subject_id
        
        # 1. Initialize filters for new IDs
        if sid not in self.states:
            self.states[sid] = {
                "kalman": KalmanFilter(dt=self.dt),
                "smoother": JointSmoother(alpha=self.alpha)
            }
            
        filters = self.states[sid]
        
        # 2. State Estimation (Kalman Filter)
        # Use centroid as the global position anchor
        centroid = np.mean(joints, axis=0) # Normalized robocentric centroid
        state_vec = filters["kalman"].update(centroid)
        
        pos_estimate, vel_estimate = filters["kalman"].get_state()

        return MotionState(
            timestamp=timestamp,
            position=pos_estimate,
            velocity=vel_estimate,
            joints=joints, # Semantically refined joints from MUL
            joint_velocities=None, 
            confidence=confidence,
            source_id=f"{source_id}:{sid}"
        )

    def reset_id(self, sid: int):
        """Clears state for a specific subject ID."""
        if sid in self.states:
            del self.states[sid]

    def reset(self):
        """Clears all subject states."""
        self.states = {}
