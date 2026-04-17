import time
from typing import Dict, Any, Optional, List
import numpy as np

from src.motion.intelligence.learning.experience import ExperienceRecorder, InteractionExperience
from src.motion.intelligence.learning.profile_manager import UserProfileManager
from src.motion.intelligence.learning.embedding import EmbeddingStore
from src.motion.intelligence.learning.reward import RewardEngine
from src.motion.intelligence.learning.policy_adapter import PolicyAdapter
from src.motion.intelligence.multimodal.state import HumanState

# CLPE V2 Hardening Modules
from src.motion.intelligence.learning.stabilizer import RewardStabilizer
from src.motion.intelligence.learning.credit import TemporalCredit
from src.motion.intelligence.learning.exploration import ExplorationStrategy

class CLPEngineV2:
    """
    Continuous Learning + Personalization Engine (CLPE V2).
    Evolved for stable, exploratory, and persistent behavioral learning.
    Includes Reward Smoothing, Temporal Credit Assignment, and Epsilon-Greedy Variations.
    """
    def __init__(self, persistence_interval: int = 300): # 300 frames ~ 15-20s at 20fps
        self.recorder = ExperienceRecorder()
        self.profile_manager = UserProfileManager()
        self.embedding_store = EmbeddingStore()
        self.reward_engine = RewardEngine()
        self.policy_adapter = PolicyAdapter()
        
        # CLPE V2 Hardening
        self.stabilizer = RewardStabilizer(window_size=10)
        self.temporal_credit = TemporalCredit(decay_factor=0.85)
        self.exploration = ExplorationStrategy(epsilon=0.1)
        
        # System State
        self.last_state: Dict[int, Dict[str, Any]] = {}
        self.persistence_interval = persistence_interval
        self.frame_counter = 0

    def process(self, user_id: int, current_state: HumanState, base_action: Dict[str, Any], motion_embedding: Optional[np.ndarray] = None) -> (Dict[str, Any], float):
        """
        Executes the Production CLPE V2 behavioral loop.
        """
        self.frame_counter += 1
        state_dict = current_state.serialize()
        
        # 1. Experience & Memory
        exp = self.recorder.record(user_id, state_dict, base_action)
        if motion_embedding is not None:
            self.embedding_store.add(user_id, motion_embedding)
            
        # 2. Raw Reward Inference
        raw_reward = self.reward_engine.compute(self.last_state.get(user_id), state_dict)
        self.last_state[user_id] = state_dict
        
        # 3. V2 Hardening: Reward Stabilization (Smoothing)
        smoothed_reward = self.stabilizer.smooth(raw_reward)
        exp.reward = smoothed_reward
        
        # 4. V2 Hardening: Temporal Credit Assignment
        # Propagates the smoothed reward backward to recent actions
        history = self.recorder.buffer.get(user_id, [])
        self.temporal_credit.assign(history, smoothed_reward)
        
        # 5. Profile Evolution (Learning step)
        profile = self.profile_manager.get_profile(user_id)
        # Intensity adaptation based on temporal-credited reward
        profile.preferred_intensity = max(0.5, min(2.2, profile.preferred_intensity + (smoothed_reward * 0.04)))
        
        # 6. Behavioral Adaptation & Exploration
        adapted_action = self.policy_adapter.adapt(base_action, profile)
        
        # V2 Hardening: Exploration Strategy (Discovery) + Safety Clipping
        final_action = self.exploration.apply(adapted_action)
        
        # 7. Periodic Persistence (as requested by user to optimize I/O)
        if self.frame_counter % self.persistence_interval == 0:
            self.profile_manager.store.save(profile)
            
        return final_action, smoothed_reward

    def force_save(self, user_id: int):
        profile = self.profile_manager.get_profile(user_id)
        self.profile_manager.store.save(profile)

    def reset_user(self, user_id: int):
        self.profile_manager.reset(user_id)
        self.stabilizer.reset()
        if user_id in self.last_state:
            del self.last_state[user_id]

    def reset_all(self):
        self.profile_manager.store.reset_all()
        self.stabilizer.reset()
        self.last_state.clear()
