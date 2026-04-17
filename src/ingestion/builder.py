import time
import uuid
from typing import Dict, Any
import numpy as np
from src.ingestion.schemas import UnifiedInputPacket, SourceType

class PacketBuilder:
    """
    Factory class to construct standardized UnifiedInputPackets.
    Ensures all metadata and sync markers are correctly assigned.
    """
    def build(self, 
              frame_normalized: np.ndarray, 
              frame_full_res: np.ndarray,
              source_type: SourceType, 
              source_id: str, 
              fps: float, 
              index: int) -> UnifiedInputPacket:
        
        return UnifiedInputPacket(
            frame_normalized=frame_normalized,
            frame_full_res=frame_full_res,
            timestamp=time.time(),
            source_type=source_type,
            source_id=source_id,
            frame_index=index,
            fps=fps,
            width=frame_full_res.shape[1],
            height=frame_full_res.shape[0],
            sync_id=str(uuid.uuid4()),
            metadata={
                "pipeline": "sign-verse-input",
                "status": "active",
                "index": index
            }
        )
