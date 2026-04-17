import time
from typing import List, Dict, Any, Optional

class IdentityStateManager:
    """
    Manages persistent subject history for social intelligence.
    Enforces a 5-subject limit and implements a reacquisition grace period.
    """
    def __init__(self, max_subjects: int = 5, grace_period_sec: float = 2.0):
        self.max_subjects = max_subjects
        self.grace_period = grace_period_sec
        self.sessions: Dict[int, Dict[str, Any]] = {}

    def update(self, subject_id: int, state: Dict[str, Any]):
        """
        Updates or initializes a session for a subject.
        """
        now = time.time()
        
        if subject_id not in self.sessions:
            # Handle max capacity (Evict least engaged if needed)
            if len(self.sessions) >= self.max_subjects:
                self._evict_least_engaged()
                
            self.sessions[subject_id] = {
                "history": [],
                "last_seen": now,
                "engagement": 0.0
            }
            
        session = self.sessions[subject_id]
        session["history"].append(state)
        session["last_seen"] = now
        session["engagement"] = state.get("engagement", 0.0)
        
        # Limit history window (30 frames ~ 1 sec)
        if len(session["history"]) > 30:
            session["history"].pop(0)

    def get_history(self, subject_id: int) -> List[Dict[str, Any]]:
        """Returns subject history if within grace period."""
        if subject_id not in self.sessions:
            return []
            
        session = self.sessions[subject_id]
        if time.time() - session["last_seen"] > self.grace_period:
            # Grace period expired
            del self.sessions[subject_id]
            return []
            
        return session["history"]

    def _evict_least_engaged(self):
        """Clears the session with the lowest engagement score."""
        if not self.sessions:
            return
        lowest_id = min(self.sessions, key=lambda k: self.sessions[k]["engagement"])
        del self.sessions[lowest_id]
