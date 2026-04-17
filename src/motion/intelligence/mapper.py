from typing import Dict, Any

class IntentActionMapper:
    """
    Maps interpreted human intents to specific robotic maneuvers or high-level behaviors.
    """
    def map_intent_to_action(self, intent: str, confidence: float) -> Dict[str, Any]:
        """
        Returns a high-level action command for the Robotics Bridge.
        """
        if confidence < 0.2:
            return {"type": "IDLE", "command": "maintain_posture"}

        if intent == "GREETING/WAVE":
            return {
                "type": "GESTURE",
                "command": "wave_hand",
                "parameters": {"speed": 1.2, "repeat": 2}
            }
        
        if intent == "GESTURE_IN_PROGRESS":
            return {"type": "TRACKING", "command": "follow_motion"}

        return {"type": "IDLE", "command": "active_wait"}
