import time
from typing import Dict, Any

class BehaviorStateMachine:
    """
    Social State Machine for HRI continuity.
    Implements 5-second hysteresis to prevent flickering in social focus.
    """
    def __init__(self, hysteresis_duration: float = 5.0):
        self.hysteresis = hysteresis_duration
        # subject_id -> {"state": str, "last_transition": float}
        self.subjects: Dict[int, Dict[str, Any]] = {}

    def update(self, subject_id: int, detected_intent: str) -> str:
        """
        Updates the social state based on intent and timing constraints.
        """
        now = time.time()
        
        if subject_id not in self.subjects:
            self.subjects[subject_id] = {
                "state": "IDLE",
                "last_transition": now
            }
            
        current = self.subjects[subject_id]
        time_in_state = now - current["last_transition"]
        
        # 1. Transition Logic: IDLE -> ENGAGED
        if current["state"] == "IDLE":
            if detected_intent in ["GREETING", "WAVE", "APPROACH", "FOLLOW_ME"]:
                current["state"] = "ENGAGED"
                current["last_transition"] = now
                
        # 2. Transition Logic: ENGAGED -> IDLE (Requires 5s Hysteresis)
        elif current["state"] == "ENGAGED":
            # Only allow disengagement if enough time has passed
            if detected_intent in ["DISENGAGE", "DEPART", "IDLE"]:
                if time_in_state >= self.hysteresis:
                    current["state"] = "IDLE"
                    current["last_transition"] = now
                    
        return current["state"]

    def clear(self, subject_id: int):
        if subject_id in self.subjects:
            del self.subjects[subject_id]
