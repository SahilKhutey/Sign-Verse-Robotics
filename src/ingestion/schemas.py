from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
import numpy as np

class SourceType(str, Enum):
    CAMERA = "camera"
    IMAGE_SEQUENCE = "image_sequence"
    VIDEO = "video_upload"
    YOUTUBE = "youtube"
    IMAGE = "image"
    STREAM = "rtsp"

class UnifiedInputPacket(BaseModel):
    """
    Canonical production-grade input packet for Sign-Verse Robotics.
    Contains both ML-ready normalized tensors and high-resolution display frames.
    """
    # Video Payloads
    frame_normalized: Any  # (640, 640, 3) np.ndarray
    frame_full_res: Any    # (H, W, 3) np.ndarray
    
    # Metadata
    timestamp: float
    source_type: SourceType
    source_id: str
    
    # Temporal Info
    frame_index: int
    fps: float
    
    # Spatial Info
    width: int
    height: int
    
    # Robotics Hooks
    calibration: Dict[str, Any] = {}
    sync_id: str
    
    # Debug / Analytics
    metadata: Dict[str, Any] = {
        "pipeline": "sign-verse-input",
        "status": "active"
    }

    class Config:
        arbitrary_types_allowed = True

class MotionSequence(BaseModel):
    sequence_id: str
    source_uri: str
    fps: float
    metadata: Dict = {}
    frames: List[Any] # Will store FrameData or MotionStates
    created_at: Any = Field(default_factory=lambda: None) # Placeholder
