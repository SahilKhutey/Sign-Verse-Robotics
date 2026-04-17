import time
from typing import Dict, Any, Optional, List
import numpy as np
from src.motion.core.state import MotionState
from src.db.schemas import FaceLandmarks
from src.motion.intelligence.multimodal.state import HumanState
from src.motion.intelligence.multimodal.emotion import EmotionExtractor
from src.motion.intelligence.multimodal.gesture import GestureContextAnalyzer
from src.motion.intelligence.multimodal.engagement import EngagementEstimator
from src.motion.intelligence.multimodal.fusion import AffectiveFusionEngine
from src.motion.intelligence.multimodal.identity import IdentityStateManager
from src.motion.intelligence.multimodal.stabilizer import EmotionStabilizer, EngagementTracker
from src.motion.intelligence.multimodal.context import TemporalContextEngine

# MAIL V3 Components
from src.motion.intelligence.multimodal.decay import EmotionDecay
from src.motion.intelligence.multimodal.reid import IdentityReID
from src.motion.intelligence.multimodal.spatial import SpatialAwarenessEngine
from src.motion.intelligence.multimodal.balancer import EngagementBalancer

from src.motion.intelligence.multimodal.mmte.engine import MMTEEngine
from src.motion.intelligence.multimodal.features import FeatureFusion
from src.motion.intelligence.stability.engine import DecisionStabilityEngine
import torch
import os

class MultimodalEngine:
    """
    HRI-Grade Multimodal Affective Intelligence Layer (MAIL V3).
    Orchestrates Identity Re-ID, Emotion Decay Models, Spatial Awareness (Robot-Base),
    and Multi-Subject Engagement Balancing.
    """
    def __init__(self):
        # Base Translators
        self.emotion_extractor = EmotionExtractor()
        self.gesture_analyzer = GestureContextAnalyzer()
        self.engagement_estimator = EngagementEstimator()
        
        # MAIL V3 Hardening (Legacy / Heuristic Backup)
        self.reid = IdentityReID(max_drift=0.6)
        self.decay_model = EmotionDecay(decay_rate=0.92)
        self.spatial_engine = SpatialAwarenessEngine()
        self.balancer = EngagementBalancer()
        
        # Temporal States
        self.identity_manager = IdentityStateManager(max_subjects=5)
        self.engagement_tracker = EngagementTracker()
        self.context_engine = TemporalContextEngine()
        self.fusion_engine = AffectiveFusionEngine()

        # MMTE: Unified Brain Integration
        self.fusion_orchestrator = FeatureFusion()
        self.mmte_model = MultiModalTransformer(n_layers=6)
        weights_path = "models/mmte/checkpoints/latest.pt"
        if os.path.exists(weights_path):
            self.mmte_model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        self.mmte_engine = MMTEEngine(self.mmte_model, seq_len=90) # 3.0s window
        
        # DSE: Deployment-Grade Stability & Safety
        self.dse = DecisionStabilityEngine(entropy_threshold=1.55, hyst_duration=5.0)

    def process(self, intent_baseline: str, state: MotionState, face: Optional[FaceLandmarks], representation_256: np.ndarray) -> HumanState:
        """
        Executes the Production MAIL V3 pipeline for a specific subject.
        """
        sid_str = state.source_id.split(":")[-1]
        raw_id = int(sid_str) if sid_str.isdigit() else 0
        
        # 1. Identity Re-ID (Stable ID matching)
        subject_id = self.reid.predict_and_match(raw_id, state.position, state.timestamp)
        
        # 2. Raw Component Extraction
        raw_emotion, e_conf = self.emotion_extractor.extract(subject_id, face)
        gesture_data = self.gesture_analyzer.analyze(state)
        raw_engagement = self.engagement_estimator.estimate(state, face)
        
        # 3. V3 Hardening: Emotion Decay (Handles occlusion better than simple locks)
        stable_emotion = self.decay_model.update(subject_id, raw_emotion, e_conf)
        stable_engagement = self.engagement_tracker.update(subject_id, raw_engagement)
        
        # 4. Spatial Awareness (Robot-Base Relative)
        spatial_data = self.spatial_engine.compute(state.position)
        
        # 5. Temporal Context Inference
        history = self.identity_manager.get_history(subject_id)
        current_context = self.context_engine.infer(history)
        
        # 6. Unified Neural Perceptual Model (MMTE)
        # 6a. Generate 345D Fused Token
        fused_token = self.fusion_orchestrator.fuse(
            representation_256, face, stable_engagement, 
            {"status": current_context}, spatial_data
        )
        
        # 6b. Neural Inference
        mmte_result = self.mmte_engine.update(subject_id, fused_token)
        
        # 6c. Deployment-Grade Stability filtering (DSE)
        # We pass the MMTE results into DSE for uncertainty and consistency checks.
        dse_action, social_state = self.dse.process(
            subject_id, 
            mmte_result["intent_probs"] if mmte_result else torch.zeros(12),
            mmte_result["intent"] if mmte_result else "UNKNOWN",
            {"speed": 1.0, "intensity": gesture_data["intensity"]} # Simulated policy action for baseline
        )
        
        # 6d. Improved Uncertainty-Gated Fallback logic
        use_backup = dse_action is None or mmte_result is None
        
        if use_backup:
            fused_intent = self.fusion_engine.fuse(
                intent_baseline, stable_emotion, current_context, stable_engagement
            )
            final_emotion = stable_emotion
            final_engagement = stable_engagement
            final_conf = (state.confidence + e_conf) / 2.0
            inference_type = "HEURISTIC_BACKUP_ENTROPY"
            final_social_state = "NEUTRAL"
        else:
            fused_intent = mmte_result["intent"] # DSE stabilizes this via majority vote internallly
            final_emotion = mmte_result["emotion"]
            final_engagement = mmte_result["engagement"]
            final_conf = (mmte_result["intent_conf"] + mmte_result["emotion_conf"]) / 2.0
            inference_type = "STABLE_TRANSFORMER"
            final_social_state = social_state
        
        # 7. Build HumanState V3.2 (Production DSE-Filtered)
        human_state = HumanState(
            timestamp=time.time(),
            subject_id=subject_id,
            intent=fused_intent,
            emotion=final_emotion,
            engagement=final_engagement,
            priority=0.0, 
            intensity=dse_action["intensity"] if dse_action else gesture_data["intensity"],
            distance=spatial_data["distance"],
            social_zone=spatial_data["zone"],
            confidence=final_conf,
            metadata={
                "context": current_context,
                "social_state": final_social_state,
                "gesture_type": gesture_data["type"],
                "robot_pos": spatial_data["pos_robot"].tolist(),
                "inference_engine": inference_type
            }
        )
        
        # 8. Persistent History Update
        self.identity_manager.update(subject_id, human_state.serialize())
        
        return human_state

    def balance_scene(self, human_states: List[HumanState]) -> List[HumanState]:
        """
        Calculates relative priority across all active human states in the scene.
        """
        serialized = [h.serialize() for h in human_states]
        balanced = self.balancer.balance(serialized)
        
        # Map balanced priority back to objects
        for i, h in enumerate(human_states):
            h.priority = balanced[i]["priority"]
            
        return human_states

    def reset_id(self, sid: int):
        self.reid.reset_id(sid)
        self.decay_model.reset_id(sid)
        self.identity_manager.update(sid, {})
