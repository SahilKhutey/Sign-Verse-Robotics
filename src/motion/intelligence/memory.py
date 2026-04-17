from collections import deque
from typing import List, Dict, Any

class BehaviorMemory:
    """
    In-memory behavior history for a specific subject ID.
    Tracks patterns of intent and action for real-time adaptation.
    """
    def __init__(self, max_history: int = 100):
        self.history = deque(maxlen=max_history)

    def store(self, intent: str, action: Dict[str, Any], confidence: float):
        """Records an intelligence event."""
        self.history.append({
            "intent": intent,
            "action": action,
            "confidence": confidence,
            "timestamp": None # Optional: Use system time if needed
        })

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Returns the last N events."""
        return list(self.history)[-n:]

    def clear(self):
        self.history.clear()
