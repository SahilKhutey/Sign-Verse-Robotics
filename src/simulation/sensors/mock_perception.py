import numpy as np
from typing import Dict, Any, Optional

class SensorSimulator:
    """
    Simulates the perception stack output (MediaPipe/YOLO).
    Injects sensor noise and occlusion artifacts for robustness testing.
    """
    def __init__(self, noise_level: float = 0.01):
        self.noise_level = noise_level

    def capture(self, human_behavior: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts ground-truth behavior into "noisy" sensor data.
        """
        landmarks = human_behavior["landmarks"]
        
        # 1. Add Gaussian Noise to skeletal data
        noisy_landmarks = landmarks + np.random.normal(0, self.noise_level, landmarks.shape)
        
        # 2. Simulate confidence jitter
        confidence = max(0.4, min(1.0, 0.9 + np.random.normal(0, 0.05)))
        
        return {
            "source_id": "sim:subject_0",
            "timestamp": human_behavior["timestamp"],
            "position": [0, 0, 1.5], # Mocked distance
            "landmarks": noisy_landmarks,
            "face": {
                "emotion": human_behavior["emotion"],
                "confidence": confidence
            },
            "engagement": human_behavior["engagement"] + np.random.normal(0, 0.02),
            "confidence": confidence
        }
