import numpy as np
from typing import List
from src.motion.core.state import MotionState

class MotionEmbedding:
    """
    Transforms a single MotionState into a high-density joint representation (Rt).
    This serves as the input token for the TIE v2 Transformer.
    """
    def encode_frame(self, state: MotionState) -> np.ndarray:
        """
        Extracts and normalizes features for a single frame.
        Rt = [joints, velocities, confidence]
        """
        if state.joints is None:
            return np.zeros(256)
            
        # 1. Flatten joints (N*3)
        features = state.joints.flatten()
        
        # 2. Add Confidence
        features = np.append(features, [state.confidence])
        
        # 3. Dynamic Padding/Truncating to target dimension 256
        if len(features) > 256:
            features = features[:256]
        else:
            features = np.pad(features, (0, 256 - len(features)), 'constant')
            
        return features

    def encode_sequence(self, sequence: List[MotionState]) -> np.ndarray:
        """ Legacy support for mean-based encoding. """
        frames = [self.encode_frame(s) for s in sequence]
        return np.mean(frames, axis=0) if frames else np.zeros(256)
