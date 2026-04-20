import yaml
import os
import torch
from typing import Dict, Any, Tuple, List
from src.motion.intelligence.rl.ppo import PPOAgent
from src.motion.intelligence.rl.encoder import StateEncoder
from src.motion.intelligence.rl.sds.mode import RLMode, DeploymentController
from src.motion.intelligence.rl.sds.exploration import ExplorationController
from src.motion.intelligence.rl.sds.safety import SafetyConstraintLayer
from src.motion.intelligence.rl.sds.manager import PolicyVersionManager
from src.motion.intelligence.rl.tcl.monitor import HealthMonitor
from src.motion.intelligence.rl.tcl.logger import ExplainabilityLogger
from src.motion.intelligence.rl.tcl.override import HumanOverrideController
from src.motion.intelligence.rl.tcl.drift import DriftDetector
from src.motion.intelligence.multimodal.state import HumanState

class RLPolicyEngine:
    """
    Real-Time Inference Engine for learned RL Social Policies.
    Bridges unified human affective states to optimal robotic actions.
    """
    def __init__(self, config_path: str = "config/rl_config.yaml"):
        # 1. Load Config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # 2. Base Components
        self.encoder = StateEncoder()
        self.agent = PPOAgent(self.config)
        
        # 3. RL-SDS: Safety & Deployment Stack
        self.mode_ctrl = DeploymentController(RLMode.LIVE)
        self.explorer = ExplorationController(live_eps=0.05) # "Moderate" epsilon as requested
        self.safety = SafetyConstraintLayer()
        self.version_mgr = PolicyVersionManager(self.agent.actor)
        
        # 4. RL-TCL: Trust & Control Stack
        self.health_monitor = HealthMonitor()
        self.logger = ExplainabilityLogger()
        self.override = HumanOverrideController()
        self.drift_detector = DriftDetector()
        
        # 5. Action Map
        self.ACTION_IDS = [0, 1, 2, 3, 4, 5]
        self.ACTION_MAP = {
            0: "IDLE", 1: "WAVE", 2: "GREETING", 3: "POINTING", 4: "STOP", 5: "FOLLOW"
        }
        
        # 5. Load Weights if Available
        checkpoint_path = "models/rl_policy/checkpoints/latest.pt"
        if os.path.exists(checkpoint_path):
            self.agent.load(checkpoint_path)

    def decide(self, human_state: HumanState) -> Dict[str, Any]:
        """
        Input: Multimodal HumanState
        Output: Explainable, Hardened, and Controllable Action
        """
        # 1. Perception Stability check
        current_stab = human_state.metadata.get("stability", 1.0)
        
        # 2. Neural Action Selection
        state_tensor = self.encoder.encode(human_state)
        with torch.no_grad():
            base_idx, log_prob = self.agent.select_action(state_tensor, stochastic=False)
            confidence = float(torch.exp(log_prob).item())
            
        # 3. RL-SDS: Apply Exploration & Safety
        action_idx = self.explorer.get_action(base_idx, self.ACTION_IDS, self.mode_ctrl.mode)
        safe_idx = self.safety.enforce(action_idx, human_state)
        
        # 4. RL-TCL: Health & Drift Monitoring
        self.health_monitor.track(human_state.engagement, current_stab, safe_idx)
        self.drift_detector.update(human_state.engagement)
        
        if self.health_monitor.should_rollback() or self.drift_detector.detect():
            self.version_mgr.load_version("v1.0") # Revert to stable baseline
            
        # 5. Result Resolution
        action_name = self.ACTION_MAP.get(safe_idx, "IDLE")
        
        base_action = {
            "intent": action_name,
            "policy_type": "TRUST_CONTROL_RLAP",
            "confidence": confidence,
            "safety_override": safe_idx != action_idx
        }
        
        # 6. RL-TCL: Human Override & Audit Logging
        final_action = self.override.apply(base_action)
        
        self.logger.log({
            "action": final_action["intent"],
            "conf": confidence,
            "eng": human_state.engagement,
            "stab": current_stab,
            "is_manual": final_action.get("is_manual", False)
        })
        
        return final_action
