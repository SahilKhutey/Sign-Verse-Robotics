from typing import Dict, Any, Optional

class HumanOverrideController:
    """
    Master Manual Override for Sign-Verse Robotics.
    Latching Mode: Stays in manual control until explicitly released by human operator.
    """
    def __init__(self):
        self._manual_action: Optional[str] = None
        self._is_active = False

    def request_override(self, action_name: str):
        """Operator forces a specific behavior."""
        self._manual_action = action_name
        self._is_active = True
        print(f"🧑✈️ HUMAN OVERRIDE ACTIVE: Robot forced to '{action_name}'")

    def release_override(self):
        """Returns control to the autonomous AI stack."""
        self._manual_action = None
        self._is_active = False
        print("🧑✈️ HUMAN OVERRIDE RELEASED: Autonomy restored.")

    def apply(self, autonomous_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intercepts autonomous output.
        If override is latched, returns the manual action instead.
        """
        if self._is_active and self._manual_action:
            return {
                "intent": self._manual_action,
                "policy_type": "HUMAN_OPERATOR_OVERRIDE",
                "is_manual": True
            }
            
        return autonomous_action
