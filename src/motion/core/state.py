from dataclasses import dataclass
import numpy as np
from typing import Optional, List, Dict, Any

@dataclass
class MotionState:
    """
    Canonical motion state S_t for Sign-Verse Robotics.
    Standardized for robotics perception and state estimation.
    """
    timestamp: float

    # Global position (root centroid / pelvis tracking)
    position: np.ndarray        # (3,) -> [x, y, z]

    # Global linear velocity estimate
    velocity: np.ndarray        # (3,) -> [vx, vy, vz]

    # Full skeleton joint capture (3D landmarks)
    # Shape: (N, 3) where N depends on the model (e.g., 33 for Pose, 21 for Hand)
    joints: Optional[np.ndarray] = None

    # Temporal joint velocities (delta joints / dt)
    joint_velocities: Optional[np.ndarray] = None

    # Aggregate confidence score (0.0 - 1.0)
    confidence: float = 0.0

    # Source identifier (job_id, camera_id)
    source_id: str = "unknown"

    # State uncertainty (Noise Covariance from Kalman Filter)
    covariance: Optional[np.ndarray] = None

    # Auxiliary tracking/debug payload
    metadata: Optional[Dict[str, Any]] = None

    def serialize(self):
        """Helper to convert numpy arrays for JSON transmission."""
        return {
            "timestamp": self.timestamp,
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "joints": self.joints.tolist() if self.joints is not None else None,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "metadata": self.metadata or {}
        }
