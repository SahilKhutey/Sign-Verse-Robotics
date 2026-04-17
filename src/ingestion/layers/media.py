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

        # 2. Numerical Normalization (0-255 uint8 to 0-1 float32)
        # Standardizing bit depth for platform-wide consistency
        normalized_frame = frame.astype(np.float32) / 255.0

        data["frame"] = normalized_frame
        return data
