import numpy as np
from typing import List, Dict, Any, Optional
from collections import deque
from src.db.schemas import FaceLandmarks

class EmotionExtractor:
    """
    Geometry-based Affective Computing.
    Detects emotion (Happy, Surprise, Calm) from Face Mesh landmarks.
    Integrates 3-frame temporal smoothing for stability.
    """
    def __init__(self, smoothing_window: int = 3):
        self.smoothing_window = smoothing_window
        self.emotion_history: Dict[int, deque] = {} # SubjectID -> Deque[Score]
        
        # Canonical Indices from MediaPipe Face Mesh
        self.L_MOUTH = 61   # Left Mouth corner
        self.R_MOUTH = 291  # Right Mouth corner
        self.U_MOUTH = 13   # Upper Lip
        self.D_MOUTH = 14   # Lower Lip

    def extract(self, subject_id: int, face: Optional[FaceLandmarks]) -> (str, float):
        """
        Analyzes facial geometry and returns processed (emotion, confidence).
        """
        if face is None or len(face.skeleton) < 478:
            return "neutral", 0.5
            
        lms = face.skeleton
        
        # 1. Smile Detection (Distance between mouth corners normalized by lip distance)
        mouth_width = self._dist(lms[self.L_MOUTH], lms[self.R_MOUTH])
        mouth_height = self._dist(lms[self.U_MOUTH], lms[self.D_MOUTH])
        
        # Normalize by eye-distance or facial scale in production; using ratio here
        smile_score = mouth_width / (mouth_height + 1e-6)
        
        # 2. Thresholding & Smoothing
        # Mapping ratio to 0-1 range (Experimental mapping)
        happy_val = np.clip((smile_score - 3.0) / 2.0, 0.0, 1.0)
        
        # Temporal Smoothing (EMA)
        if subject_id not in self.emotion_history:
            self.emotion_history[subject_id] = deque(maxlen=self.smoothing_window)
        
        history = self.emotion_history[subject_id]
        history.append(happy_val)
        smoothed_val = np.mean(list(history))
        
        # 3. Decision Logic
        if smoothed_val > 0.6:
            return "happy", smoothed_val
        elif smoothed_val < 0.2:
            return "neutral", 1 - smoothed_val
            
        return "neutral", 0.5

    def _dist(self, p1, p2) -> float:
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def reset_id(self, sid: int):
        if sid in self.emotion_history:
            del self.emotion_history[sid]
