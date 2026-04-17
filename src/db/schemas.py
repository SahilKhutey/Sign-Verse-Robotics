from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Joint(BaseModel):
    x: float
    y: float
    z: float
    visibility: float
    presence: Optional[float] = None

class HandLandmarks(BaseModel):
    skeleton: List[Joint]
    handedness: str  # 'Left' or 'Right'
    score: float

class FaceLandmarks(BaseModel):
    skeleton: List[Joint]  # 478 points for MediaPipe FaceMesh

class PoseLandmarks(BaseModel):
    skeleton: List[Joint]  # 33 points for MediaPipe Pose

class HumanSubject(BaseModel):
    subject_id: int
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    pose: Optional[PoseLandmarks] = None
    face: Optional[FaceLandmarks] = None
    left_hand: Optional[HandLandmarks] = None
    right_hand: Optional[HandLandmarks] = None

class FrameData(BaseModel):
    frame_index: int
    timestamp: float
    subjects: List[HumanSubject] = []
    detected_objects: Optional[List[Dict]] = []

class MotionSequence(BaseModel):
    sequence_id: str
    source_uri: str
    fps: float
    metadata: Dict = {}
    frames: List[FrameData]
    created_at: datetime = Field(default_factory=datetime.now)

class RobotAction(BaseModel):
    """
    Converted format for robotics training.
    Mapping joint angles to specific robot DOF.
    """
    frame_index: int
    joint_angles: Dict[str, float]
    velocity: Optional[Dict[str, float]] = None
    acceleration: Optional[Dict[str, float]] = None
