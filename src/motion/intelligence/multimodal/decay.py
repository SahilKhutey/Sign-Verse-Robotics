from typing import Dict, Tuple, Optional

class EmotionDecay:
    """
    Implements a temporal decay model for human emotions.
    Prevents 'frozen' emotions during occlusions or low-confidence tracking.
    """
    def __init__(self, decay_rate: float = 0.9, reset_threshold: float = 0.3):
        self.decay_rate = decay_rate
        self.reset_threshold = reset_threshold
        # subject_id -> (emotion, strength)
        self.states: Dict[int, Tuple[str, float]] = {}

    def update(self, subject_id: int, emotion: str, confidence: float) -> str:
        """
        Updates the emotion state with decay logic.
        """
        if subject_id not in self.states:
            self.states[subject_id] = (emotion, 1.0)
            return emotion

        prev_emotion, strength = self.states[subject_id]

        # 1. Update logic based on perception confidence
        if confidence < 0.4:
            # Low confidence: Decay the previous emotion strength
            strength *= self.decay_rate
        else:
            # High confidence: Update to new emotion and reset strength
            prev_emotion = emotion
            strength = 1.0

        # 2. Reset to neutral if strength is too low
        if strength < self.reset_threshold:
            prev_emotion = "neutral"
            strength = 0.0

        self.states[subject_id] = (prev_emotion, strength)
        return prev_emotion

    def reset_id(self, sid: int):
        if sid in self.states:
            del self.states[sid]
