from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class HumanState:
    """
    HRI-Grade Multimodal Affective Human State (V3).
    Includes Spatial Awareness, Relative Priority, and Identity Stability.
    """
    timestamp: float
    subject_id: int
    
    # Core Intelligence
    intent: str
    emotion: str
    
    # Quantitative Dynamics
    engagement: float # 0.0 - 1.0 (Temporal Smooth)
    priority: float   # 0.0 - 1.0 (Normalized across crowd)
    intensity: float  # 0.0 - 2.0 (Energy)
    
    # Spatial Context (Proxemics)
    distance: float   # Real-world meters from Robot Base
    social_zone: str  # INTIMATE, SOCIAL, PUBLIC
    
    # Metadata
    confidence: float
    metadata: Dict[str, Any] # stability, context, etc.

    def serialize(self):
        return {
            "timestamp": self.timestamp,
            "subject_id": self.subject_id,
            "intent": self.intent,
            "emotion": self.emotion,
            "engagement": round(self.engagement, 2),
            "priority": round(self.priority, 2),
            "intensity": round(self.intensity, 2),
            "distance": round(self.distance, 2),
            "social_zone": self.social_zone,
            "confidence": round(self.confidence, 2)
        }
