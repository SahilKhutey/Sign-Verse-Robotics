from typing import Dict, Any, Optional
from src.ingestion.schemas import UnifiedInputPacket

class FrameExtractor:
    """
    Production Layer 1: Frame Extraction.
    Standardizes raw packets into a processing-ready dictionary.
    """
    def extract(self, packet: UnifiedInputPacket) -> Optional[Dict[str, Any]]:
        # Integrity check: Ensure frame data exists
        if packet.frame_normalized is None:
            return None

        return {
            "frame": packet.frame_normalized,
            "timestamp": packet.timestamp,
            "source_id": packet.source_id,
            "source_type": packet.source_type,
            "fps": packet.fps,
            "resolution": (packet.width, packet.height),
            "metadata": packet.metadata
        }
