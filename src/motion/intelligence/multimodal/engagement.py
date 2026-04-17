import numpy as np
from typing import Optional, Dict, Any
from src.db.schemas import FaceLandmarks
from src.motion.core.state import MotionState

class EngagementEstimator:
    """
    Estimates user participation level (0.0 - 1.0).
    Fuses Head-Pose Attention + Motion Intensity.
    """
    def __init__(self, motion_weight: float = 0.5, attention_weight: float = 0.5):
        self.motion_weight = motion_weight
        self.attention_weight = attention_weight
        
        # Landmark indices for head orientation
        self.NOSE = 1
        self.L_EYE = 33
        self.R_EYE = 263

    def estimate(self, state: MotionState, face: Optional[FaceLandmarks]) -> float:
        """
        Calculates a real-time engagement score.
        """
        # 1. Motion Component (Active movement increases engagement)
        velocity = np.linalg.norm(state.velocity)
        motion_score = np.clip(velocity / 1.5, 0.0, 1.0) # Normalized to max velocity
        
        # 2. Attention Component (Looking toward the camera/robot)
        attention_score = 0.3 # Baseline for no-face
        
        if face:
            # Simple attention heuristic: 
            # Are the eyes/nose centered? (Using relative coords from crop)
            lms = face.skeleton
            eye_center = (lms[self.L_EYE].x + lms[self.R_EYE].x) / 2.0
            
            # Distance from center-screen (MediaPipe coords 0.5 is centered)
            off_center = abs(eye_center - 0.5)
            # 1.0 = looking directly; 0.0 = looking away
            attention_score = np.clip(1.0 - (off_center * 4.0), 0.0, 1.0)
            
        # 3. Weighted Fusion
        return (motion_score * self.motion_weight) + (attention_score * self.attention_weight)
