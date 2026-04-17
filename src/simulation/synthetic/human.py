import random
import numpy as np
from typing import Dict, Any

class SyntheticHuman:
    """
    Simulated Human Agent for Sign-Verse Simulation.
    Supports 'CLIP_DRIVEN' (animation playback) and 'GAN_DRIVEN' (procedural/generative) modes.
    """
    def __init__(self, mode: str = "HYBRID"):
        self.mode = mode
        self.emotion_pool = ["happy", "neutral", "angry", "surprise", "sad"]
        self.intent_pool = ["wave", "point", "stop", "idle", "approach", "depart"]
        
    def generate_behavior(self) -> Dict[str, Any]:
        """
        Generates a virtual human state including intent, emotion, and engagement dynamics.
        """
        # Select sub-mode if HYBRID
        active_mode = random.choice(["CLIP", "GAN"]) if self.mode == "HYBRID" else self.mode
        
        # 1. High-level Social State
        intent = random.choice(self.intent_pool)
        emotion = random.choice(self.emotion_pool)
        engagement = random.uniform(0.3, 1.0)
        
        # 2. Motion Data Generation
        if active_mode == "CLIP":
            # In a real system, this would index into a BVH/FBX library
            landmarks = self._get_clip_landmarks(intent)
        else:
            # GAN/Generative proxy (Perlin noise-based procedural motion)
            landmarks = self._generate_gan_motion(intent)
            
        return {
            "mode": active_mode,
            "intent": intent,
            "emotion": emotion,
            "engagement": engagement,
            "landmarks": landmarks,
            "timestamp": np.datetime64('now')
        }

    def _get_clip_landmarks(self, intent: str) -> np.ndarray:
        """Mock animation clip lookup."""
        return np.ones((33, 3)) * 0.5 # Placeholder for actual clip data

    def _generate_gan_motion(self, intent: str) -> np.ndarray:
        """Generative/Procedural motion synthesis."""
        noise = np.random.normal(0, 0.05, (33, 3))
        base = np.zeros((33, 3))
        return base + noise
