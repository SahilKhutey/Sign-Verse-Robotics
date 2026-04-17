import logging
from typing import Dict, Any

# Configure logger for diagnostics
logger = logging.getLogger("stability.validator")

class ActionValidator:
    """
    Final Safety Validator for robotic actions.
    Enforces hardware-safe limits and emits diagnostic errors when clipped.
    """
    def __init__(self):
        # Hardware limits [min, max]
        self.LIMITS = {
            "intensity": (0.2, 2.2),
            "speed": (0.2, 2.2)
        }

    def validate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clamps intensity and speed. Logs an ERROR if values are out of bounds.
        """
        for param, (min_v, max_v) in self.LIMITS.items():
            if param in action:
                val = float(action[param])
                if val < min_v or val > max_v:
                    # User requirement: Throw a diagnostic error/log
                    logger.error(f"SAFETY_VIOLATION: Decision Engine output {param}={val} exceeds limits [{min_v}, {max_v}]. Enforcing safety clip.")
                    action[param] = max(min_v, min(max_v, val))
        
        return action
