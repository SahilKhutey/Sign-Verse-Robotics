import cv2
import numpy as np
from typing import Dict, Any

class MediaNormalizer:
    """
    Production Layer 3: Media Normalization.
    Transforms raw pixel buffers into model-ready RGB float32 tensors.
    """
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        frame = data["frame"]

        # 1. Colorspace Conversion (BGR to RGB)
        # MediaPipe and most deep learning models expect RGB
        if frame.ndim == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 2. Numerical Normalization (REMOVED)
        # Note: Scaling to float32 [0, 1] is moved to individual model wrappers
        # to prevent global pipeline breakage where models expect uint8 0-255.
        
        data["frame"] = frame # Keep as uint8 for perception processing
        return data
