import numpy as np
from typing import Optional, List, Dict
from src.db.schemas import HumanSubject, Joint

class SkeletonFusion:
    """
    Unified multi-modal skeleton fusion engine.
    Merges Pose (33), Hands (2x21), and Face anchors into a canonical point cloud.
    """
    def fuse(self, subject: HumanSubject) -> (np.ndarray, np.ndarray):
        """
        Combines disparate perception sources into a single fused landmark vector.
        Returns: (joints (N, 3), confidences (N,))
        """
        joints_list = []
        confidences_list = []

        # 1. Pose (Core Body) - 33 Landmarks
        if subject.pose:
            p_joints = np.array([[j.x, j.y, j.z] for j in subject.pose.skeleton])
            p_conf = np.array([j.visibility for j in subject.pose.skeleton])
            joints_list.append(p_joints)
            confidences_list.append(p_conf)
        else:
            # Fallback zeros for the core body
            joints_list.append(np.zeros((33, 3)))
            confidences_list.append(np.zeros(33))

        # 2. Left Hand (21 Landmarks)
        if subject.left_hand:
            l_joints = np.array([[j.x, j.y, j.z] for j in subject.left_hand.skeleton])
            l_conf = np.ones(21) * subject.left_hand.score
            joints_list.append(l_joints)
            confidences_list.append(l_conf)
        else:
            joints_list.append(np.zeros((21, 3)))
            confidences_list.append(np.zeros(21))

        # 3. Right Hand (21 Landmarks)
        if subject.right_hand:
            r_joints = np.array([[j.x, j.y, j.z] for j in subject.right_hand.skeleton])
            r_conf = np.ones(21) * subject.right_hand.score
            joints_list.append(r_joints)
            confidences_list.append(r_conf)
        else:
            joints_list.append(np.zeros((21, 3)))
            confidences_list.append(np.zeros(21))

        # 4. Face Anchors (Nose / Forehead) - Optional
        if subject.face:
            # Use specific head anchors from Face Mesh (e.g., nose tip)
            # index 1 is nose tip in MediaPipe Face Mesh
            f_joints = np.array([[subject.face.skeleton[1].x, subject.face.skeleton[1].y, subject.face.skeleton[1].z]])
            f_conf = np.ones(1)
            joints_list.append(f_joints)
            confidences_list.append(f_conf)
        else:
            joints_list.append(np.zeros((1, 3)))
            confidences_list.append(np.zeros(1))

        return np.concatenate(joints_list, axis=0), np.concatenate(confidences_list, axis=0)

class JointConfidenceFusion:
    """
    Applies weighted confidence blending to the fused skeleton.
    Smoothly dampens occluded or low-confidence joints.
    """
    def apply(self, joints: np.ndarray, confidences: np.ndarray) -> np.ndarray:
        """
        Dampens low-confidence joint noise.
        """
        # We don't want to completely zero out low confidence points (could cause spikes)
        # Instead, we pull them toward the global mean or previous state (not handling here)
        # For now, let's just weigh the influence of the joint
        weights = np.expand_dims(confidences, axis=1)
        return joints * weights
