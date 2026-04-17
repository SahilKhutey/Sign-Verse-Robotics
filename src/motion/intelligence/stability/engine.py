from typing import Dict, Any, Optional, Tuple
import torch
from src.motion.intelligence.stability.uncertainty import UncertaintyEstimator
from src.motion.intelligence.stability.temporal import TemporalFilter
from src.motion.intelligence.stability.behavior import BehaviorStateMachine
from src.motion.intelligence.stability.validator import ActionValidator

class DecisionStabilityEngine:
    """
    Unified Decision Stability Engine (DSE).
    Hardens neural intelligence for real-world robotics deployment.
    Orchestrates Uncertainty Detection, Temporal Smoothing, and Social State Continuity.
    """
    def __init__(self, entropy_threshold: float = 1.6, hyst_duration: float = 5.0):
        self.uncertainty = UncertaintyEstimator(entropy_threshold=entropy_threshold)
        self.temporal = TemporalFilter(window_size=7)
        self.behavior = BehaviorStateMachine(hysteresis_duration=hyst_duration)
        self.validator = ActionValidator()

    def process(self, 
                subject_id: int, 
                intent_probs: torch.Tensor, 
                intent_name: str, 
                proposed_action: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Executes the DSE stability flow.
        Returns (FinalAction, SocialState).
        If the neural model is uncertain, FinalAction will be None (signal for fallback).
        """
        # 1. Uncertainty Guard (Information Entropy)
        # If the model is confused, we force a fallback to heuristics
        if self.uncertainty.is_uncertain(intent_probs):
            return None, "NEUTRAL"
            
        # 2. Temporal Smoothing (Anti-Jitter)
        smoothed_intent = self.temporal.smooth(subject_id, intent_name)
        
        # 3. Behavioral Continuity (5s Hysteresis)
        social_state = self.behavior.update(subject_id, smoothed_intent)
        
        # 4. Action Validation (Hardware Safety pass)
        final_action = self.validator.validate(proposed_action)
        
        return final_action, social_state

    def clear(self, subject_id: int):
        self.temporal.clear(subject_id)
        self.behavior.clear(subject_id)
