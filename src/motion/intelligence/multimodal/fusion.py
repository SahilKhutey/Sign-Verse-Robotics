from typing import List, Dict, Any, Optional

class AffectiveFusionEngine:
    """
    Multimodal Logic Fusion Engine (V2).
    Combines Intent + Emotion + Context + Engagement into high-fidelity social states.
    """
    def fuse(self, intent: str, emotion: str, context: str, engagement: float) -> str:
        """
        Applies contextual social rules to determine the final interaction state.
        """
        # Rule 1: High Engagement Priority
        if engagement > 0.8 and emotion == "happy":
            return f"ENTHUSIASTIC_{intent}"
            
        # Rule 2: Sustained Interaction
        if context == "ONGOING_INTERACTION":
            return f"SUSTAINED_{intent}"
            
        # Rule 3: Graceful Disengagement
        if context == "DISENGAGING":
            return "SOFT_DISMISSAL"
            
        # Rule 4: Affective Override
        if intent == "GREETING/WAVE":
            if emotion == "happy":
                return "FRIENDLY_GREETING"
            return "FORMAL_GREETING"
            
        return intent
