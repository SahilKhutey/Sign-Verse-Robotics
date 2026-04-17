import cv2
import numpy as np
from typing import Tuple, Optional

class GPUAccelerator:
    """
    Optional acceleration layer for high-speed spatial normalization.
    Uses PyTorch/CUDA if available, falls back to OpenCV/CPU.
    """
    def __init__(self):
        self.device = "cpu"
        self._torch = None
        
        # Try dynamic import to keep base install lightweight
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                self._torch = torch
                print(f"[GPUAccelerator] CUDA backend activated (v{torch.version.cuda})")
            else:
                self.device = "cpu"
        except ImportError:
            self.device = "cpu"

    def resize(self, frame: np.ndarray, target_size: Tuple[int, int] = (640, 640)) -> np.ndarray:
        """
        Accelerated bilinear interpolation for frame resizing.
        """
        if self.device == "cuda" and self._torch:
            try:
                # Convert to tensor and move to GPU
                # Assumption: frame is in HWC (OpenCV default)
                tensor = self._torch.from_numpy(frame).to(self.device).float()
                
                # Permute to NCHW for torch interpolate
                # [H, W, C] -> [1, C, H, W]
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)
                
                # Resample
                tensor = self._torch.nn.functional.interpolate(
                    tensor, 
                    size=target_size, 
                    mode='bilinear', 
                    align_corners=False
                )
                
                # Back to HWC and CPU for downstream MediaPipe (which often expects CPU)
                # Note: In a pure-GPU pipeline, we'd keep it on the card.
                return tensor.squeeze(0).permute(1, 2, 0).byte().cpu().numpy()
                
            except Exception as e:
                print(f"[GPUAccelerator Warning] Fallback triggered: {e}")
                return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)

        # CPU Fallback
        return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
