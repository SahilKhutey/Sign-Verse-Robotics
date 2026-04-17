from typing import Dict, Any, Optional
from src.motion.intelligence.learning.profile import UserProfile
from src.motion.intelligence.learning.store import ProfileStore
from src.motion.intelligence.learning.experience import InteractionExperience

class UserProfileManager:
    """
    Manages the long-term evolution of user behavioral profiles.
    Implements momentum-based updates (0.9 history / 0.1 new) for natural adaptive behavior.
    """
    def __init__(self, momentum: float = 0.9):
        self.store = ProfileStore()
        self.momentum = momentum

    def update_from_experience(self, exp: InteractionExperience) -> UserProfile:
        """
        Updates the persistent profile based on a single interaction experience.
        """
        uid = exp.user_id
        profile = self.store.get(uid)
        
        # 1. Update Interaction Metrics
        profile.total_interactions += 1
        
        # 2. Update Engagement Averaging (Momentum-based)
        current_engagement = exp.state.get("engagement", 0.0)
        profile.avg_engagement = (self.momentum * profile.avg_engagement) + \
                                ((1.0 - self.momentum) * current_engagement)
        
        # 3. Intensity Adaptation (Slow evolution toward user's activity level)
        # Note: True learning logic happens in the LearningEngine/RewardEngine,
        # here we manage the state accumulation.
        
        # Save updated profile
        self.store.save(profile)
        return profile

    def get_profile(self, user_id: int) -> UserProfile:
        return self.store.get(user_id)

    def reset(self, user_id: int):
        self.store.reset_profile(user_id)
