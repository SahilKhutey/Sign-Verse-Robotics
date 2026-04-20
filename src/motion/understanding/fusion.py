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

        pose_points = None
        if subject.pose:
            pose_points = np.array([[j.x, j.y, j.z] for j in subject.pose.skeleton], dtype=np.float32)

        # 1. Pose (Core Body) - 33 Landmarks
        if subject.pose:
            p_joints = pose_points
            p_conf = np.array([max(float(j.visibility), 0.05) for j in subject.pose.skeleton], dtype=np.float32)
            joints_list.append(p_joints)
            confidences_list.append(p_conf)
        else:
            # Fallback zeros for the core body
            joints_list.append(np.zeros((33, 3), dtype=np.float32))
            confidences_list.append(np.zeros(33, dtype=np.float32))

        # 2. Left Hand (21 Landmarks)
        if subject.left_hand:
            l_joints = np.array([[j.x, j.y, j.z] for j in subject.left_hand.skeleton], dtype=np.float32)
            l_conf = np.ones(21, dtype=np.float32) * max(float(subject.left_hand.score), 0.2)
            joints_list.append(l_joints)
            confidences_list.append(l_conf)
        else:
            fallback_left = self._hand_fallback(pose_points, wrist_index=15)
            joints_list.append(fallback_left)
            confidences_list.append(np.ones(21, dtype=np.float32) * (0.15 if pose_points is not None else 0.0))

        # 3. Right Hand (21 Landmarks)
        if subject.right_hand:
            r_joints = np.array([[j.x, j.y, j.z] for j in subject.right_hand.skeleton], dtype=np.float32)
            r_conf = np.ones(21, dtype=np.float32) * max(float(subject.right_hand.score), 0.2)
            joints_list.append(r_joints)
            confidences_list.append(r_conf)
        else:
            fallback_right = self._hand_fallback(pose_points, wrist_index=16)
            joints_list.append(fallback_right)
            confidences_list.append(np.ones(21, dtype=np.float32) * (0.15 if pose_points is not None else 0.0))

        # 4. Face Anchors (Nose / Forehead) - Optional
        if subject.face:
            # Use specific head anchors from Face Mesh (e.g., nose tip)
            # index 1 is nose tip in MediaPipe Face Mesh
            f_joints = np.array([[subject.face.skeleton[1].x, subject.face.skeleton[1].y, subject.face.skeleton[1].z]], dtype=np.float32)
            f_conf = np.ones(1, dtype=np.float32)
            joints_list.append(f_joints)
            confidences_list.append(f_conf)
        else:
            joints_list.append(self._face_fallback(pose_points))
            confidences_list.append(np.array([0.15 if pose_points is not None else 0.0], dtype=np.float32))

        return np.concatenate(joints_list, axis=0), np.concatenate(confidences_list, axis=0)

    def _hand_fallback(self, pose_points: Optional[np.ndarray], wrist_index: int) -> np.ndarray:
        if pose_points is None or wrist_index >= len(pose_points):
            return np.zeros((21, 3), dtype=np.float32)
        wrist = pose_points[wrist_index]
        return np.repeat(wrist[None, :], 21, axis=0).astype(np.float32)

    def _face_fallback(self, pose_points: Optional[np.ndarray]) -> np.ndarray:
        if pose_points is None:
            return np.zeros((1, 3), dtype=np.float32)
        if len(pose_points) > 0 and np.linalg.norm(pose_points[0]) > 0:
            return pose_points[0:1].astype(np.float32)
        head_anchor = np.mean(pose_points[[11, 12]], axis=0, keepdims=True)
        return head_anchor.astype(np.float32)

class JointConfidenceFusion:
    """
    Applies weighted confidence blending to the fused skeleton.
    Smoothly dampens occluded or low-confidence joints.
    """
    def apply(self, joints: np.ndarray, confidences: np.ndarray) -> np.ndarray:
        """
        Dampens low-confidence joint noise.
        """
        if joints.size == 0:
            return joints
        anchor = np.median(joints[:33], axis=0) if len(joints) >= 33 else np.median(joints, axis=0)
        weights = np.expand_dims(np.clip(confidences, 0.15, 1.0), axis=1)
        return (weights * joints) + ((1.0 - weights) * anchor)
