from dataclasses import dataclass
import numpy as np
from typing import Tuple, Dict, Any

@dataclass
class StructuredFrame:
    """
    Final canonical frame structure for Sign-Verse Robotics.
    Ready for downstream fusion, learning, and robotics control.
    """
    # Normalized Tensor Data
    frame: np.ndarray  # float32 [0, 1] RGB
    timestamp: float

    # Temporal Intelligence
    sequence_id: str
    sequence_index: int
    time_delta: float  # dt desde el último frame

    # Source Attribution
    source_id: str
    source_type: str

    # Media Metadata (Normalized)
    fps: float
    resolution: Tuple[int, int]

    # Enriched Metadata
    is_keyframe: bool
    pipeline_stage: str = "ingestion"
    
    # Traceability
    metadata: Dict[str, Any] = None
