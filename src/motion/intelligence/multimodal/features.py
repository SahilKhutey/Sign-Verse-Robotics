import numpy as np
from typing import Dict, Any, Optional
from src.motion.core.state import MotionState
from src.db.schemas import FaceLandmarks

class FeatureFusion:
    """
    Multimodal Token Generator for MMTE.
    Packs motion, face, engagement, context, and spatial signals into a 345D unified vector.
    """
    def __init__(self):
        # Indices for strategic Face Landmarks (Mouth, Eyes, Eyebrows)
        # We pick 21 landmarks * 3 coordinates (x,y,z) = 63D + 1D (face presence) = 64D
        self.FACE_INDICES = [
            0, 13, 14, 17, # Lips
            33, 133, 159, 145, # Left Eye
            263, 362, 386, 374, # Right Eye
            70, 107, 300, 336, # Eyebrows
            1, 4, # Nose
            61, 291, 152 # Jaw/Chin
        ]

    def fuse(self, 
             motion_256: np.ndarray, 
             face: Optional[FaceLandmarks], 
             engagement: float, 
             context_data: Dict[str, Any],
             spatial_data: Dict[str, Any]) -> np.ndarray:
        """
        Concatenates all modalities into a single 345D token.
        """
        # 1. Face (64D)
        face_64 = np.zeros(64)
        if face and len(face.skeleton) >= 478:
            pts = []
            for idx in self.FACE_INDICES:
                p = face.skeleton[idx]
                pts.extend([p.x, p.y, p.z])
            face_64[:63] = pts
            face_64[63] = 1.0 # Presence bit
            
        # 2. Engagement (1D)
        eng_1 = np.array([engagement])
        
        # 3. Context (16D)
        # Simply encoding status strings/history into a fixed-size vector
        ctx_16 = np.zeros(16)
        ctx_map = {"IDLE": 0, "USER_ENGAGED": 1, "NEUTRAL": 2, "GREETING": 3}
        status = context_data.get("status", "NEUTRAL")
        ctx_16[ctx_map.get(status, 2)] = 1.0 
        
        # 4. Spatial (8D)
        # [dist, dx, dy, dz, zone_one_hot_4]
        spatial_8 = np.zeros(8)
        spatial_8[0] = spatial_data.get("distance", 0.0)
        pos = spatial_data.get("pos_robot", [0, 0, 0])
        spatial_8[1:4] = pos[:3]
        zone_map = {"INTIMATE": 4, "SOCIAL": 5, "PUBLIC": 6, "UNKNOWN": 7}
        spatial_8[zone_map.get(spatial_data.get("zone"), 7)] = 1.0

        # 5. Final Concatenation
        # 256 + 64 + 1 + 16 + 8 = 345
        return np.concatenate([
            motion_256,
            face_64,
            eng_1,
            ctx_16,
            spatial_8
        ])
