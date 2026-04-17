import cv2
import glob
import os
import uuid
import time
from typing import Generator, Dict, Any
from src.ingestion.base import BaseInputEngine
from src.ingestion.schemas import UnifiedInputPacket, SourceType

class ImageSequenceLoader(BaseInputEngine):
    """
    Standardizes image sequences (from folders) into a temporal motion stream.
    """
    def __init__(self, folder_path: str, target_fps: float = 30.0):
        super().__init__(source_id=str(uuid.uuid4()), target_fps=target_fps)
        self.folder_path = folder_path
        self.image_paths = sorted(glob.glob(os.path.join(folder_path, "*")))
        
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "folder_path": self.folder_path,
            "image_count": len(self.image_paths),
            "target_fps": self.target_fps
        }

    def stream(self) -> Generator[UnifiedInputPacket, None, None]:
        self.is_running = True
        
        for idx, img_path in enumerate(self.image_paths):
            if not self.is_running:
                break
                
            frame = cv2.imread(img_path)
            if frame is None:
                continue

            yield UnifiedInputPacket(
                video_id=self.source_id,
                frame=frame,
                frame_index=idx,
                timestamp=idx / self.target_fps,
                source_type=SourceType.IMAGE_SEQUENCE,
                fps=self.target_fps,
                metadata=self.get_metadata()
            )

    def stop(self):
        super().stop()
