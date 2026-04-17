from typing import List, Dict, Any

class TemporalContextEngine:
    """
    Infers sustained social context from intent history.
    Enables the robot to distinguish between isolated gestures and sessions.
    """
    def infer(self, history: List[Dict[str, Any]]) -> str:
        """
        Analyzes recent subject history to determine contextual state.
        """
        if not history:
            return "NEUTRAL"
            
        # Extract intent sequence
        intents = [h.get("intent", "IDLE") for h in history]
        
        # 1. Ongoing Interaction Detection
        # If the user has been greeting or active for several frames
        greeting_count = sum(1 for i in intents if "GREETING" in i)
        if greeting_count > 5:
            return "ONGOING_INTERACTION"
            
        # 2. Disengagement Detection
        # If the last few intents have returned to IDLE
        if len(intents) >= 5 and all(i == "IDLE" for i in intents[-3:]):
            return "DISENGAGING"
            
        # 3. Active Engagement
        if intents[-1] != "IDLE":
            return "ACTIVE"
            
        return "NEUTRAL"
