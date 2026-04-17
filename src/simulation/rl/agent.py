import torch
import torch.nn as nn
from typing import Dict, Any
from src.motion.intelligence.pipeline import IntelligencePipeline

class RLAgentWrapper:
    """
    Reinforcement Learning Wrapper for the Sign-Verse AI Stack.
    Enables dual-level gradient descent for both MMTE (Perception) and Policy (Decision).
    """
    def __init__(self, pipeline: IntelligencePipeline):
        self.pipeline = pipeline
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Optimization Targets
        # Level 1: MMTE (Unified Multimodal Understanding)
        self.mmte_optimizer = torch.optim.Adam(self.pipeline.multimodal.mmte_model.parameters(), lr=1e-4)
        
        # Level 2: Decision Policy (Action Selection)
        # Note: In a production RL setup, this would be a Policy Network (Actor-Critic)
        # For now, we wrap the baseline parameters.
        self.policy_optimizer = torch.optim.Adam(self.pipeline.policy.parameters() if hasattr(self.pipeline.policy, 'parameters') else [], lr=1e-3)

    def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the full AI pipeline on simulated sensor data.
        """
        # Convert simulated observation to MotionState
        from src.motion.core.state import MotionState
        state = MotionState(
            source_id=observation["source_id"],
            timestamp=time.time(), # Simulation clock
            position=observation["position"],
            landmarks=observation["landmarks"],
            confidence=observation["confidence"]
        )
        
        # Run Pipeline (AIE -> MAIL -> MMTE -> DSE -> CLPE)
        human_state = self.pipeline.process(state, subject_id=0, face=observation["face"])
        
        return {
            "intent": human_state.intent,
            "emotion": human_state.emotion,
            "engagement": human_state.engagement,
            "action": human_state.metadata.get("action", {})
        }

    def learn(self, loss_val: torch.Tensor):
        """
        Executes backpropagation across both perception and decision layers.
        """
        self.mmte_optimizer.zero_grad()
        self.policy_optimizer.zero_grad()
        
        loss_val.backward()
        
        self.mmte_optimizer.step()
        self.policy_optimizer.step()
        
    def save_checkpoint(self, path: str):
        torch.save({
            "mmte": self.pipeline.multimodal.mmte_model.state_dict(),
            "policy": self.pipeline.policy.state_dict() if hasattr(self.pipeline.policy, 'state_dict') else None
        }, path)
