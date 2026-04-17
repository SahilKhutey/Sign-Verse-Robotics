import numpy as np
from typing import Dict, Any, Optional
from src.motion.understanding.temporal import TemporalSmoothing
from src.motion.understanding.fusion import SkeletonFusion, JointConfidenceFusion
from src.motion.understanding.refiner import MotionRefiner
from src.motion.understanding.normalizer import KinematicNormalizer
from src.db.schemas import HumanSubject

class MotionUnderstandingEngine:
    """
    The orchestrator for the Motion Understanding Layer (MUL).
    Sequences fusion, temporal refinement, and kinematic normalization.
    """
    def __init__(self):
        self.fusion = SkeletonFusion()
        self.confidence_fusion = JointConfidenceFusion()
        self.temporal = TemporalSmoothing(window_size=5)
        self.refiner = MotionRefiner(deviation_threshold=0.5)
        self.normalizer = KinematicNormalizer()

    def process(self, subject: HumanSubject) -> (np.ndarray, float):
        """
        Executes the full Motion Understanding pipeline for a single subject.
        Returns: (normalized_joints (N, 3), collective_confidence)
        """
        sid = subject.subject_id
        
        # 1. Multi-modal Fusion (Pose + Hands + Face anchors)
        raw_joints, confidences = self.fusion.fuse(subject)
        
        # 2. Confidence-Weighted Blending
        blended_joints = self.confidence_fusion.apply(raw_joints, confidences)
        
        # 3. Temporal Window Smoothing
        smoothed_joints = self.temporal.apply(sid, blended_joints)
        
        # 4. Spike Refinement (Outlier suppression)
        refined_joints = self.refiner.refine(smoothed_joints)
        
        # 5. Kinematic Normalization (Robocentric space)
        normalized_joints = self.normalizer.normalize(refined_joints)
        
        # Calculate a collective confidence score for the subject
        avg_confidence = np.mean(confidences)
        
        return normalized_joints, avg_confidence

    def reset_id(self, sid: int):
        self.temporal.reset_id(sid)
