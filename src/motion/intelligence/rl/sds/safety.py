from typing import Dict, Any, List
from collections import deque
from src.motion.intelligence.multimodal.state import HumanState

class SafetyConstraintLayer:
    """
    Hard-threshold safety overrides for RL Action Selection.
    Enforces social distance ethics and prevents high-frequency repetitive gestures.
    """
    def __init__(self, history_len: int = 10):
        self.action_history = deque(maxlen=history_len)
        self.ACTION_MAP_INV = {
            "IDLE": 0, "WAVE": 1, "GREETING": 2, "POINTING": 3, "STOP": 4, "FOLLOW": 5
        }

    def enforce(self, action_idx: int, human: HumanState) -> int:
        """
        Intercepts the RL action and applies HRI constraints.
        Returns the original or overridden action index.
        """
        action_name = self._idx_to_name(action_idx)
        
        # 1. Proximity Constraint (Intimate Zone Safety)
        # If user is too close, block aggressive/large movements
        if human.distance < 0.6: # 60cm threshold
            if action_name in ["WAVE", "FOLLOW"]:
                print(f"🛡️ SDS Override: '{action_name}' blocked in intimate zone.")
                return self.ACTION_MAP_INV["IDLE"]

        # 2. Anti-Spam Constraint (Repetition Penalty)
        # If we just performed this action 3 times, switch to IDLE
        repeat_count = list(self.action_history).count(action_idx)
        if repeat_count > 3:
            print(f"🛡️ SDS Override: Action spam detected ('{action_name}'). Throttling.")
            return self.ACTION_MAP_INV["IDLE"]

        # 3. Low Stability Fallback
        # If perception is jittery, do not execute complex social gestures
        if human.metadata.get("stability", 1.0) < 0.35:
            return self.ACTION_MAP_INV["IDLE"]

        self.action_history.append(action_idx)
        return action_idx

    def _idx_to_name(self, idx: int) -> str:
        names = ["IDLE", "WAVE", "GREETING", "POINTING", "STOP", "FOLLOW"]
        return names[idx] if 0 <= idx < len(names) else "IDLE"
