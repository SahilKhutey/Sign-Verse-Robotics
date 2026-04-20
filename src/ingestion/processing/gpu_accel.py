import cv2
import numpy as np
from typing import Tuple, Optional

class GPUAccelerator:
    """
    Advanced acceleration layer for high-speed spatial normalization.
    Uses PyTorch/CUDA if available, falls back to OpenCV/CPU.
    
    SMOOTHING UPDATE: 
    Only uses GPU for high-resolution images (>= 720p). 
    Small frames (640x640) use CPU to avoid device transfer latency.
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
                print(f"[GPUAccelerator] CUDA backend optimized & activated (v{torch.version.cuda})")
            else:
                self.device = "cpu"
        except ImportError:
            self.device = "cpu"

    def resize(self, frame: np.ndarray, target_size: Tuple[int, int] = (640, 640)) -> np.ndarray:
        """
        Accelerated bilinear interpolation for frame resizing.
        Smart selection based on resolution to minimize latency.
        """
        h, w = frame.shape[:2]
        
        # High-Resolution Thresholding:
        # Resizing 640x640 is faster on CPU due to PCIe transfer overhead.
        # Only use GPU for 720p, 1080p, or 4K streams.
        if self.device == "cuda" and self._torch and (h >= 720 or w >= 1280):
            try:
                # Convert to tensor and move to GPU
                tensor = self._torch.from_numpy(frame.copy()).to(self.device).float()
                
                # Permute to NCHW: [H, W, C] -> [1, C, H, W]
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)
                
                # Resample
                tensor = self._torch.nn.functional.interpolate(
                    tensor, 
                    size=target_size, 
                    mode='bilinear', 
                    align_corners=False
                )
                
                # Back to HWC and CPU
                return tensor.squeeze(0).permute(1, 2, 0).byte().cpu().numpy()
                
            except Exception as e:
                # print(f"[GPUAccelerator Warning] Fallback triggered: {e}")
                return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)

        # CPU optimized path for standard ML frames
        return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
