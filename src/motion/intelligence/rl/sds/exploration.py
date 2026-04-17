import random
from typing import List, Any
from src.motion.intelligence.rl.sds.mode import RLMode

class ExplorationController:
    """
    Manages action exploration (epsilon-stochasticity) for RL.
    User Preference: 'low not very low close to medium' for LIVE mode (~0.05).
    """
    def __init__(self, 
                 train_eps: float = 0.25, 
                 live_eps: float = 0.05):
        self.train_eps = train_eps
        self.live_eps = live_eps

    def get_action(self, computed_action: int, action_space: List[int], mode: RLMode) -> int:
        """
        Applies epsilon-greedy exploration if stochasticity is permitted.
        """
        epsilon = self.train_eps if mode == RLMode.TRAIN else self.live_eps
        
        if random.random() < epsilon:
            # Exploration: Random social action
            return random.choice(action_space)
            
        # Exploitation: Model-derived optimal action
        return computed_action
