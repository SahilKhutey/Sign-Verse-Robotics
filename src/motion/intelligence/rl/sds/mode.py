from enum import Enum
from typing import Dict, Any

class RLMode(Enum):
    TRAIN = "TRAIN"  # High exploration, active weight updates
    LIVE = "LIVE"    # Low exploration, restricted updates, safety priority

class DeploymentController:
    """
    Manages the global operational mode of the RL intelligence stack.
    Controls behavior consistency and learning persistence.
    """
    def __init__(self, initial_mode: RLMode = RLMode.LIVE):
        self.mode = initial_mode

    def set_mode(self, mode: RLMode):
        self.mode = mode
        print(f"🛡️ RL System Mode Switched to: {self.mode.value}")

    @property
    def is_training(self) -> bool:
        return self.mode == RLMode.TRAIN

    @property
    def is_live(self) -> bool:
        return self.mode == RLMode.LIVE
