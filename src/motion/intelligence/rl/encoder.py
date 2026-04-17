import numpy as np
import torch
from typing import Dict, Any
from src.motion.intelligence.multimodal.state import HumanState

class StateEncoder:
    """
    Condenses the HRI-Grade HumanState (V3.2) into a numerical RL state vector.
    Normalizes spatial and affective dynamics for stable neural network input.
    """
    def __init__(self):
        self.INTENT_MAP = {
            "IDLE": 0, "GREETING": 1, "POINTING": 2, "STOP": 3, "WAVE": 4,
            "THANK_YOU": 5, "DISENGAGE": 6, "APPROACH": 7, "DEPART": 8,
            "REQUEST_HELP": 9, "FOLLOW_ME": 10, "UNKNOWN": 11
        }
        self.EMOTION_MAP = {
            "neutral": 0, "happy": 1, "sad": 2, "angry": 3, "surprise": 4
        }

    def encode(self, human: HumanState) -> torch.Tensor:
        """
        Input: HumanState Object
        Output: 6D Torch Tensor [Intent_Norm, Emotion_Norm, Eng, Dist, Priority, Stability]
        """
        intent_val = self.INTENT_MAP.get(human.intent, 11) / 12.0
        emotion_val = self.EMOTION_MAP.get(human.emotion, 0) / 5.0
        
        # Distance Clipping (0-10m -> 0.0-1.0)
        dist_norm = min(1.0, human.distance / 10.0)
        
        # Stability check from metadata
        stability = human.metadata.get("stability", 1.0)
        
        state_vec = [
            intent_val,
            emotion_val,
            human.engagement,
            dist_norm,
            human.priority,
            stability
        ]
        
        return torch.tensor(state_vec, dtype=torch.float32)
