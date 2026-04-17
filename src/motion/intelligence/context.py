from typing import List, Dict, Any

class ContextEngine:
    """
    Infers high-level context from behavioral history.
    Transitions system state based on motion patterns.
    """
    def __init__(self):
        self.context_states = ["NEUTRAL", "USER_ENGAGED", "URGENT", "REPETITIVE"]

    def infer(self, history: List[Dict[str, Any]]) -> str:
        """
        Analyzes recent history to determine current contextual state.
        """
        if not history:
            return "NEUTRAL"

        recent_intents = [h["intent"] for h in history[-10:]]
        
        # Rule: If multiple greetings in a short window, the user is 'ENGAGED'
        if recent_intents.count("GREETING/WAVE") >= 2:
            return "USER_ENGAGED"
        
        # Rule: If high activity persists, it's 'URGENT' or focused
        # (This can be refined with velocity/displacement data in the future)
        
        return "NEUTRAL"
