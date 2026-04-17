import cv2
import numpy as np
import time
from typing import Tuple, Optional
from src.ingestion.processing.gpu_accel import GPUAccelerator

class FrameNormalizer:
    """
    Hard-locked Normalization Bus for Sign-Verse Robotics.
    Ensures spatial determinism (640x640) and temporal consistency (30fps).
    
    UPGRADED: Now supports dynamic GPU acceleration.
    """
    def __init__(self, target_size: Tuple[int, int] = (640, 640), target_fps: float = 30.0):
        self.target_size = target_size
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.last_capture_time = 0.0
        
        # New: GPU Acceleration Layer
        self.gpu = GPUAccelerator()

    def should_capture(self, current_time: float) -> bool:
        """
        Temporal Gating: Only allows frames at the target FPS.
        """
        if current_time - self.last_capture_time < self.frame_interval:
            return False
        
        self.last_capture_time = current_time
        return True

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """
        Resize frame to ML-ready target resolution using GPU if available.
        """
        return self.gpu.resize(frame, self.target_size)

    def process(self, frame: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """
        Full processing pipeline for a single frame.
        """
        if frame is None:
            return None
            
        now = time.time()
        if not self.should_capture(now):
            return None
            
        return self.normalize(frame)
