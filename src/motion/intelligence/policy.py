from typing import Dict, Any

class AdaptivePolicy:
    """
    Translates Intent + Context into a modulated robotic response.
    Replaces static mapping with dynamic behavior scaling.
    """
    def decide(self, intent: str, context: str, base_confidence: float) -> Dict[str, Any]:
        """
        Synthesizes an action command optimized for the current human context.
        """
        if intent == "IDLE":
            return {"command": "stow_posture", "intensity": 1.0}

        # Base Action from Intent
        action = {"command": "wave_hand", "intensity": 1.0, "speed": 1.0}
        
        if intent == "GREETING/WAVE":
            action["command"] = "wave_hand"
        elif intent == "GESTURE_IN_PROGRESS":
            action["command"] = "look_at_subject"
        
        # Contextual Modulation
        if context == "USER_ENGAGED":
            # Amplify response if the user is focused/engaged
            action["intensity"] = 1.6
            action["speed"] = 1.3
        elif context == "NEUTRAL":
            action["intensity"] = 1.0
            action["speed"] = 0.8 # More subtle to avoid startling
            
        return action

    def apply_adaptation(self, action: Dict[str, Any], adaptation: Dict[str, float]) -> Dict[str, Any]:
        """
        Modulates the base decision with user-specific learned preferences.
        """
        # Apply learned intensity weight
        action["intensity"] *= adaptation.get("intensity_weight", 1.0)
        action["speed"] *= adaptation.get("speed_weight", 1.0)
        
        # Clip to safe limits
        action["intensity"] = float(max(0.2, min(2.5, action["intensity"])))
        action["speed"] = float(max(0.2, min(2.5, action["speed"])))
        
        return action
