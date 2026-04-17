import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class InteractionExperience:
    """
    Transient data structure for a single interaction frame.
    """
    user_id: int
    timestamp: float
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float = 0.0

class ExperienceRecorder:
    """
    Short-term transient buffer for HRI experiences.
    Maintains privacy by using a sliding window and avoiding disk persistence for raw state.
    """
    def __init__(self, max_buffer_size: int = 1000):
        self.max_buffer_size = max_buffer_size
        # subject_id -> List[InteractionExperience]
        self.buffer: Dict[int, List[InteractionExperience]] = {}

    def record(self, user_id: int, state: Dict[str, Any], action: Dict[str, Any]) -> InteractionExperience:
        """
        Records a new interaction experience into the transient buffer.
        """
        exp = InteractionExperience(
            user_id=user_id,
            timestamp=time.time(),
            state=state,
            action=action
        )
        
        if user_id not in self.buffer:
            self.buffer[user_id] = []
            
        subject_buffer = self.buffer[user_id]
        subject_buffer.append(exp)
        
        # Enforce buffer limit (Privacy + Memory management)
        if len(subject_buffer) > self.max_buffer_size:
            subject_buffer.pop(0)
            
        return exp

    def get_recent(self, user_id: int, count: int = 10) -> List[InteractionExperience]:
        """Retrieves the most recent N experiences for a user."""
        if user_id not in self.buffer:
            return []
        return self.buffer[user_id][-count:]
