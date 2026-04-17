from typing import Dict, Any, Optional

class RewardEngine:
    """
    Quantifies the success of a robotic action through affective feedback.
    Infers a 'Reward' signal based on changes in human engagement and emotion.
    """
    def compute(self, prev_state: Optional[Dict[str, Any]], current_state: Dict[str, Any]) -> float:
        """
        Calculates a reward value (-1.0 to 1.0).
        Positive reward: Engagement rising, Emotion improving.
        Negative reward: Engagement dropping, User startled/disengaged.
        """
        if prev_state is None:
            return 0.0
            
        # 1. Engagement Delta (Primary Sigal)
        e_delta = current_state.get("engagement", 0.0) - prev_state.get("engagement", 0.0)
        
        # 2. Emotional Valence Modifier
        p_emo = prev_state.get("emotion", "neutral")
        c_emo = current_state.get("emotion", "neutral")
        
        emo_bonus = 0.0
        if p_emo == "neutral" and c_emo == "happy":
            emo_bonus = 0.5  # Significant success
        elif p_emo == "happy" and c_emo == "neutral":
            emo_bonus = -0.3 # Lost engagement
            
        # 3. Final Reward Calculation
        # Reward = (Engagement Delta) + (Emotional Valence)
        reward = e_delta + emo_bonus
        
        return float(max(-1.0, min(1.0, reward)))
