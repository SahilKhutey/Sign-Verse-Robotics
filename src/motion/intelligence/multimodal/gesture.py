import numpy as np
from typing import Dict, Any, Optional
from src.motion.core.state import MotionState

class GestureContextAnalyzer:
    """
    Refines intent based on motion dynamics.
    Quantifies 'Energy' and 'Style' of the current motion sequence.
    """
    def __init__(self, energy_threshold: float = 0.5):
        self.energy_threshold = energy_threshold

    def analyze(self, state: MotionState) -> Dict[str, Any]:
        """
        Computes dynamic motion characteristics.
        """
        # Calculate velocity magnitude for global motion
        v_mag = np.linalg.norm(state.velocity)
        
        # Energy status mapping
        if v_mag > self.energy_threshold * 2.0:
            gesture_type = "energetic"
            intensity_scale = 1.8
        elif v_mag > self.energy_threshold:
            gesture_type = "normal"
            intensity_scale = 1.2
        else:
            gesture_type = "calm"
            intensity_scale = 0.8
            
        return {
            "type": gesture_type,
            "intensity": intensity_scale,
            "velocity": v_mag,
            "confidence": 0.9 # Dynamic confidence could use variance over N frames
        }
