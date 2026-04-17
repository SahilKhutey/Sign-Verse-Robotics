from typing import Optional
from src.ingestion.schemas import UnifiedInputPacket
from src.ingestion.structured_frame import StructuredFrame
from src.ingestion.layers.extractor import FrameExtractor
from src.ingestion.layers.router import TemporalRouter
from src.ingestion.layers.media import MediaNormalizer
from src.ingestion.layers.enricher import MetadataEnricher

class IngestionPipeline:
    """
    Main Orchestrator for the Ingestion Pipeline.
    Sequentially transforms raw packets into structured temporal signals.
    """
    def __init__(self):
        self.extractor = FrameExtractor()
        self.router = TemporalRouter()
        self.normalizer = MediaNormalizer()
        self.enricher = MetadataEnricher(keyframe_interval=3)

    def process_packet(self, packet: UnifiedInputPacket) -> Optional[StructuredFrame]:
        """
        Executes the full ingestion processing chain.
        """
        # Layer 1: Extract
        data = self.extractor.extract(packet)
        if data is None:
            return None

        # Layer 2: Route (Temporal indexing)
        data = self.router.route(data)

        # Layer 3: Normalize (RGB float32)
        data = self.normalizer.normalize(data)

        # Layer 4: Enrich (Keyframes)
        data = self.enricher.enrich(data)

        # Final Construction
        return StructuredFrame(**data)
