import cv2
import uuid
from typing import Generator, Dict, Any
from src.ingestion.base import BaseInputEngine
from src.ingestion.schemas import UnifiedInputPacket, SourceType

class StreamAdapter(BaseInputEngine):
    """
    Handles network streams (RTSP, RTMP, HTTP) for CCTV and Drone integration.
    """
    def __init__(self, stream_url: str, target_fps: float = 30.0):
        super().__init__(source_id=str(uuid.uuid4()), target_fps=target_fps)
        self.stream_url = stream_url
        self.cap = cv2.VideoCapture(stream_url)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "stream_url": self.stream_url,
            "backend": "ffmpeg" # Default for network streams in cv2
        }

    def stream(self) -> Generator[UnifiedInputPacket, None, None]:
        self.is_running = True
        frame_index = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                # In a production stream, we might want to retry/reconnect here
                break

            yield UnifiedInputPacket(
                video_id=self.source_id,
                frame=frame,
                frame_index=frame_index,
                timestamp=0.0, # Will be set by normalizer/real-time sync
                source_type=SourceType.STREAM,
                fps=self.target_fps,
                metadata=self.get_metadata()
            )
            frame_index += 1

    def stop(self):
        super().stop()
        self.cap.release()
