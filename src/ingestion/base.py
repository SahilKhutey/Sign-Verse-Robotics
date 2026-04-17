from abc import ABC, abstractmethod
from typing import Generator, Dict, Any
from src.ingestion.schemas import UnifiedInputPacket

class BaseInputEngine(ABC):
    """
    Abstract Base Class for all Sign-Verse Ingestion Adapters.
    """
    def __init__(self, source_id: str, target_fps: float = 30.0):
        self.source_id = source_id
        self.target_fps = target_fps
        self.is_running = False

    @abstractmethod
    def stream(self) -> Generator[UnifiedInputPacket, None, None]:
        """
        Generator yielding standardized UnifiedInputPackets.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns source-specific metadata (resolution, device info, etc).
        """
        pass

    def stop(self):
        self.is_running = False
