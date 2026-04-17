from dataclasses import dataclass, field
from typing import List, Dict, Any
import time

@dataclass
class UserProfile:
    """
    Persistent social profile for a human subject.
    Learns and stores interaction preferences to enable 'multi-robot' continuity.
    """
    subject_id: int
    created_at: float = field(default_factory=time.time)
    
    # Learned Preferences
    preferred_intensity: float = 1.0 # 0.5 - 2.0
    preferred_speed: float = 1.0
    
    # Interaction Metrics
    total_interactions: int = 0
    avg_engagement: float = 0.0
    
    # Session History (Sliding window of last actions for feedback)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def serialize(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "created_at": self.created_at,
            "preferences": {
                "intensity": round(self.preferred_intensity, 2),
                "speed": round(self.preferred_speed, 2)
            },
            "metrics": {
                "total_interactions": self.total_interactions,
                "avg_engagement": round(self.avg_engagement, 2)
            }
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'UserProfile':
        return cls(
            subject_id=data["subject_id"],
            created_at=data["created_at"],
            preferred_intensity=data["preferences"]["intensity"],
            preferred_speed=data["preferences"]["speed"],
            total_interactions=data["metrics"]["total_interactions"],
            avg_engagement=data["metrics"]["avg_engagement"]
        )
