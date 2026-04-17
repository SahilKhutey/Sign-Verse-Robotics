from typing import Dict, Any
from src.motion.intelligence.multimodal.state import HumanState

class SocialRewardEngine:
    """
    HRI Social Alignment Reward Function.
    Maps affective state deltas and goal achievement into a scalar reward for RL.
    """
    def __init__(self):
        self.EMOTION_REWARDS = {
            "happy": 0.5,
            "neutral": 0.1,
            "surprise": 0.2,
            "sad": -0.3,
            "angry": -0.8
        }
        self.last_action = None
        self.repetition_count = 0

    def compute(self, 
                prev_human: HumanState, 
                current_human: HumanState, 
                action_type: str) -> float:
        """
        Rewards:
        1. Engagement Delta (Positive if robot response captured attention)
        2. Emotion Resonance (Positive for positive emotions)
        3. Action Consistency (Social alignment)
        """
        reward = 0.0
        
        # 1. Engagement Delta (Weight: 2.0)
        eng_delta = current_human.engagement - prev_human.engagement
        reward += (eng_delta * 2.0)
        
        # 2. Affective Value
        reward += self.EMOTION_REWARDS.get(current_human.emotion, 0.0)
        
        # 3. Penalize Extreme Disengagement
        if current_human.engagement < 0.15:
            reward -= 0.5
            
        # 4. Success bonus: Engagement high and emotion happy
        if current_human.engagement > 0.8 and current_human.emotion == "happy":
            reward += 1.0
            
        # 5. HARDENING: Anti-Spam Penalty
        if action_type == self.last_action:
            self.repetition_count += 1
            if self.repetition_count > 2:
                reward -= (0.2 * self.repetition_count) # Increasing penalty for repetition
        else:
            self.repetition_count = 0
        self.last_action = action_type
        
        # 6. HARDENING: Proximity Breach Penalty
        if current_human.distance < 0.5: # 50cm too close
            reward -= 0.4
            
        return float(reward)
