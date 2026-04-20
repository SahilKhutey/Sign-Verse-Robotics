import numpy as np
from typing import List, Optional
from src.motion.core.state import MotionState

class MotionEmbedding:
    """
    Transforms MotionState into high-density joint representations.
    SMOOTHING UPDATE: Specialized Hand Embedding for Gesture Lab.
    """
    def encode_frame(self, state: MotionState) -> np.ndarray:
        """
        Extracts and normalizes features for a single frame.
        Rt = [joints, velocities, confidence]
        """
        if state.joints is None:
            return np.zeros(256)
            
        features = state.joints.flatten()
        features = np.append(features, [state.confidence])
        
        if len(features) > 256:
            features = features[:256]
        else:
            features = np.pad(features, (0, 256 - len(features)), 'constant')
            
        return features

    def encode_hand(self, hand_landmarks: np.ndarray) -> np.ndarray:
        """
        Generates an 'Accurate' Hand Embedding (64-dim).
        Invariant to global position and scale.
        Logic: 
        1. Center on Wrist (J0).
        2. Normalize by Palm Breadth (J5-J17 distance).
        3. Flatten 21 landmarks [x,y,z] + confidence.
        """
        if hand_landmarks.shape[0] < 21:
            return np.zeros(64)

        # 1. Translation Invariance (Center at Wrist)
        wrist = hand_landmarks[0]
        centered = hand_landmarks - wrist
        
        # 2. Scale Invariance (Normalize by Palmer span)
        # Distance between Index Proximal (5) and Pinky Proximal (17)
        span = np.linalg.norm(hand_landmarks[5] - hand_landmarks[17])
        if span > 1e-6:
            normalized = centered / span
        else:
            normalized = centered
            
        # 3. Flatten and Pad to 64
        vector = normalized.flatten()
        
        if len(vector) > 64:
            vector = vector[:64]
        else:
            vector = np.pad(vector, (0, 64 - len(vector)), 'constant')
            
        return vector

    def encode_sequence(self, sequence: List[MotionState]) -> np.ndarray:
        frames = [self.encode_frame(s) for s in sequence]
        return np.mean(frames, axis=0) if frames else np.zeros(256)
