import numpy as np
from typing import Optional

class KinematicNormalizer:
    """
    Translates raw perception coordinates into a robocentric-normalized space.
    Centers the body at the torso and scales it by anatomical height.
    """
    def normalize(self, joints: np.ndarray) -> np.ndarray:
        """
        Processes (N, 3) joints into a centered, scaled coordinate space.
        """
        if joints.size == 0:
            return joints

        pose_joint_count = min(len(joints), 33)
        pose_joints = joints[:pose_joint_count]
        if pose_joint_count == 0:
            return joints

        torso_indices = [11, 12, 23, 24]
        valid_torso = [idx for idx in torso_indices if idx < pose_joint_count and np.linalg.norm(pose_joints[idx]) > 1e-5]
        valid_pose = pose_joints[np.linalg.norm(pose_joints, axis=1) > 1e-5]

        if valid_torso:
            root = np.mean(pose_joints[valid_torso], axis=0)
        elif len(valid_pose) > 0:
            root = np.mean(valid_pose, axis=0)
        else:
            root = np.zeros(3, dtype=joints.dtype)

        centered = joints - root

        shoulder_indices = [idx for idx in [11, 12] if idx < pose_joint_count and np.linalg.norm(pose_joints[idx]) > 1e-5]
        hip_indices = [idx for idx in [23, 24] if idx < pose_joint_count and np.linalg.norm(pose_joints[idx]) > 1e-5]
        if shoulder_indices and hip_indices:
            shoulder_mean = np.mean(pose_joints[shoulder_indices], axis=0)
            hip_mean = np.mean(pose_joints[hip_indices], axis=0)
            scale = np.linalg.norm(shoulder_mean - hip_mean)
        elif len(valid_pose) > 1:
            pose_extent = np.max(valid_pose, axis=0) - np.min(valid_pose, axis=0)
            scale = max(float(np.linalg.norm(pose_extent)), 1e-3)
        else:
            scale = 1.0

        scale = max(float(scale), 1e-3)
        normalized = centered / scale
        return normalized
