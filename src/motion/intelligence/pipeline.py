from src.motion.core.state import MotionState
from src.motion.intelligence.buffer import TemporalBuffer
from src.motion.intelligence.segmenter import ActionSegmenter
from src.motion.intelligence.embedding import MotionEmbedding
from src.motion.intelligence.context import ContextEngine
from src.motion.intelligence.policy import AdaptivePolicy
from src.motion.intelligence.learning.engine import CLPEngineV2
from src.motion.intelligence.memory import BehaviorMemory
from src.motion.intelligence.multimodal.engine import MultimodalEngine
from src.motion.intelligence.tie.model import IntentTransformer
from src.motion.intelligence.tie.inference import IntentInferenceEngine
from src.motion.intelligence.multimodal.state import HumanState
from src.motion.intelligence.rl.inference import RLPolicyEngine
from src.robotics.kinematics.solvers import KinematicsEngine
from src.robotics.retargeting.engine import RetargetEngine
from src.robotics.morphology.mapper import MorphologyMapper
from src.robotics.dataset.builder import DemonstrationBuilder
from src.robotics.wbc.balance.estimators import COMEstimator, ZMPEstimator
from src.robotics.wbc.control.stabilizer import BalanceController, WBCSolver
from src.robotics.wbmpc.model.full_dynamics import FullBodyDynamics
from src.robotics.wbmpc.contact.planner import ContactPlanner, ContactState
from src.robotics.wbmpc.solver.qp_optimizer import WBMPCSolver
from src.robotics.wbc.trajectory.generator import TrajectoryGenerator
from src.db.schemas import FaceLandmarks
from typing import Dict, Any, Optional, List
import torch
import os

class IntelligencePipeline:
    """
    Adaptive Intent Understanding Engine (AIE).
    Sequences motion analysis with long-term memory and context awareness.
    Supports multi-subject tracking via internalized ID states.
    """
    def __init__(self, segment_threshold: float = 0.02):
        self.default_threshold = segment_threshold
        
        # Shared computation engines
        self.embedder = MotionEmbedding()
        
        # TIE v2: Transformer Intent Engine
        self.tie_model = IntentTransformer(n_classes=7)
        weights_path = "models/tie_v2/checkpoints/latest.pt"
        if os.path.exists(weights_path):
            self.tie_model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        self.tie_engine = IntentInferenceEngine(self.tie_model)
        
        self.policy = RLPolicyEngine()
        self.context_engine = ContextEngine()
        self.multimodal = MultimodalEngine()
        self.clpe = CLPEngineV2()
        
        # 4. PRS: Production Robotics Stack
        self.retargeter = RetargetEngine(target_profile="humanoid")
        self.morphology = MorphologyMapper()
        self.kinematics = KinematicsEngine(link_lengths=[0.4, 0.4]) # Proxy for 2-link chain
        self.dataset_logger = DemonstrationBuilder()
        
        # 5. WBC: Whole-Body Control & Balance
        self.com_engine = COMEstimator()
        self.zmp_engine = ZMPEstimator()
        self.balance_ctrl = BalanceController()
        self.wbc_solver = WBCSolver()
        self.traj_gen = TrajectoryGenerator()
        
        # 6. WBMPC: Whole-Body Contact MPC
        self.wb_dynamics = FullBodyDynamics()
        self.wb_planner = ContactPlanner()
        self.wb_contact = ContactState()
        self.wb_solver = WBMPCSolver()

        # Per-ID State Dictionaries
        self.subject_states: Dict[int, Dict[str, Any]] = {}

    def update_segmentation_threshold(self, value: float):
        """Standard tuning hook for the segmenter."""
        self.default_threshold = value
        for state in self.subject_states.values():
            state["segmenter"].update_threshold(value)

    def process(self, state: MotionState, subject_id: int, face: Optional[FaceLandmarks] = None) -> HumanState:
        """
        Executes the Adaptive Intent Engine flow + Multimodal Affective Layer.
        """
        # 0. Initialize state for new subjects
        if subject_id not in self.subject_states:
            self.subject_states[subject_id] = {
                "buffer": TemporalBuffer(max_size=60),
                "segmenter": ActionSegmenter(threshold=self.default_threshold),
                "memory": BehaviorMemory(max_history=100)
            }
        
        s_state = self.subject_states[subject_id]
        buffer = s_state["buffer"]
        segmenter = s_state["segmenter"]
        memory = s_state["memory"]

        # 1. Temporal history
        buffer.add(state)
        
        # 2. Motion Trigger
        is_significant_event = segmenter.detect_trigger(state)
        
        if not is_significant_event and not buffer.is_ready():
            return HumanState(
                timestamp=state.timestamp,
                subject_id=subject_id,
                intent="IDLE",
                emotion="NEUTRAL",
                engagement=0.0,
                priority=0.0,
                intensity=0.0,
                distance=0.0,
                social_zone="UNKNOWN",
                confidence=0.0,
                metadata={"context": "BUFFERING"}
            )

        # 3. Contextual Inference (from previous patterns)
        history = memory.get_recent(20)
        context = self.context_engine.infer(history)

        # 4. Encoding & Decoding (TIE v2 - Sequence-Aware)
        representation = self.embedder.encode_frame(state)
        intent, confidence = self.tie_engine.update(subject_id, representation)
        
        # 5. Base Decision (Policy)
        base_action = self.policy.decide(intent, context, confidence)
        
        # 6. Multimodal Fusion (MMTE / MAIL V3.1)
        human_state = self.multimodal.process(intent, state, face, representation)
        
        # 7. Adaptive Intelligence (CLPE)
        # We pass the motion sequence embedding for pattern persistence
        action, reward = self.clpe.process(subject_id, human_state, base_action, representation)
        
        # 8. Memory Storage
        memory.store(intent, action, confidence)
        
        # 9. PRS: Physical Embodiment (Embodied Intelligence Manifestation)
        # a. Retarget landmarks to robot-link-aligned state
        robot_intent = self.retargeter.retarget(human_state.metadata.get("landmarks_3d", {}))
        
        # b. Scale to robot's physical morphology
        final_joint_state = self.morphology.scale_to_robot(robot_intent, {"arm_length": 0.65})
        
        # c. Record triplet for future imitation learning sweep
        self.dataset_logger.record(
            state=human_state.to_dict(),
            action=final_joint_state,
            reward=reward
        )
        
        # d. Inject physical manifest back into human_state for export tracking
        human_state.metadata["robot_payload_raw"] = final_joint_state
        
        # 10. WBMPC: Contact-Aware Locomotion & Whole-Body Stabilization
        # a. State extraction
        com = self.com_engine.compute(final_joint_state)
        # Prediction state: [pos, vel]
        current_state = np.concatenate([com, [0, 0, 0]]) 
        
        # b. Contact Planning (Footstep Logic)
        direction = np.array([1, 0, 0]) # Default forward locomotion intent
        foot_target = self.wb_planner.plan_next_step(com, direction, self.wb_contact.state)
        
        # c. WBMPC Optimization (Motion + Force)
        acc, forces = self.wb_solver.solve(current_state, foot_target)
        
        # d. WBC Injection (Stability Health monitoring)
        zmp_actual = self.zmp_engine.compute(com, acceleration=acc)
        instability = self.balance_ctrl.check_stability(zmp_actual)
        
        stable_payload = final_joint_state
        # Inject offsets based on Optimized Acceleration & Contact Forces
        offsets = self.wbc_solver.solve(zmp_actual, target_zmp=np.array([zmp_actual[0], 0]))
        
        for link in stable_payload:
            # Scale vertical stability by contact forces
            force_scale = min(1.0, forces[2] / (75.0 * 9.81))
            stable_payload[link] = [p + o * force_scale for p, o in zip(stable_payload[link], [offsets[0], 0, offsets[1]])]
        
        # e. Manifest result
        human_state.metadata["robot_payload"] = stable_payload
        human_state.metadata["contact_forces"] = forces.tolist()
        human_state.metadata["locomotion_phase"] = self.wb_contact.state
        human_state.metadata["stability_health"] = 1.0 - instability
        human_state.metadata["wbmpc_active"] = True
        
        return human_state

    def process_scene(self, human_states: List[HumanState]) -> List[HumanState]:
        """
        Refines a set of human states with scene-wide balancing (Priority).
        """
        return self.multimodal.balance_scene(human_states)

    def calibrate(self):
        """Resets all per-ID buffers and state machines to a baseline neutral state."""
        self.subject_states.clear()
        self.clpe.reset_all()
        print("[Intelligence] Full System Calibration Complete.")

    def load_model_weights(self, path: str):
        """Swaps the active TIE Transformer weights in real-time."""
        if os.path.exists(path):
            self.tie_model.load_state_dict(torch.load(path, map_location='cpu'))
            self.tie_engine = IntentInferenceEngine(self.tie_model)
            print(f"[Intelligence] Loaded model weights from {path}")
            return True
        return False
