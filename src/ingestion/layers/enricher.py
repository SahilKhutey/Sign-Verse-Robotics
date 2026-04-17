from typing import Dict, Any

class MetadataEnricher:
    """
    Production Layer 4: Metadata Enrichment.
    Adds intelligence to the frame stream, such as keyframe detection.
    """
    def __init__(self, keyframe_interval: int = 3):
        self.keyframe_interval = keyframe_interval

    def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates higher-level metadata traits for the frame.
        """
        # 1. Sophisticated Keyframe detection (Every 3 frames per user request)
        # In future, this can be expanded with motion-magnitude logic
        index = data.get("sequence_index", 0)
        is_keyframe = (index % self.keyframe_interval == 0)

        data["is_keyframe"] = is_keyframe
        data["pipeline_stage"] = "ingestion_final"

        return data
