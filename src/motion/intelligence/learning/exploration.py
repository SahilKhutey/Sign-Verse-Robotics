import random
from typing import Dict, Any

class ExplorationStrategy:
    """
    Implements epsilon-greedy exploration for behavioral discovery.
    Periodically tries new variations of robotic intensity and speed.
    Includes 'Safety Clipping' to prevent exceeding hardware limits.
    """
    def __init__(self, epsilon: float = 0.1, variation_range: float = 0.3):
        self.epsilon = epsilon
        self.variation_range = variation_range
        
        # Hard Hardware/Safety Limits
        self.LIMITS = {
            "intensity": (0.4, 2.2),
            "speed": (0.4, 2.2)
        }

    def apply(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Randomly varies the action parameters if within epsilon chance.
        Applies safety clipping regardless of exploration.
        """
        # 1. Epsilon-Greedy Exploration
        if random.random() < self.epsilon:
            scale = 1.0 + random.uniform(-self.variation_range, self.variation_range)
            action["intensity"] = action.get("intensity", 1.0) * scale
            action["speed"] = action.get("speed", 1.0) * scale
            action["is_exploring"] = True
        else:
            action["is_exploring"] = False
            
        # 2. Safety Clipping (MANDATORY)
        for key, (min_val, max_val) in self.LIMITS.items():
            if key in action:
                action[key] = max(min_val, min(max_val, float(action[key])))
                
        return action
