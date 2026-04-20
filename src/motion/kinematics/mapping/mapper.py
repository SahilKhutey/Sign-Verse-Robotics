import numpy as np
import time
from typing import Dict, Any, Optional
from src.motion.kinematics.models.human import HumanSkeleton
from src.motion.kinematics.models.robot import UniversalHumanoidModel

class JointMapper:
    """
    Kinematic Mapping Engine.
    Maps 3D human landmark geometry to standardized robotic JointState.
    Supports dynamic heuristics: Smoothing, Dampening, and IK Priority.
    """
    def __init__(self, robot_model: UniversalHumanoidModel):
        self.robot = robot_model
        
        # Heuristics Config (Adjustable via Dashboard)
        self.config = {
            "smoothing_factor": 0.4, # 0.0 to 1.0 (Higher = smoother/laggier)
            "ik_numerical_weight": 0.5, # Balance analytical/numerical
            "joint_limit_hardness": 0.9,
            "damping": 0.05
        }
        
        # State memory for smoothing
        self.last_angles: Dict[str, float] = {}
        
        # Landmark Indices (MediaPipe Holistic/Pose)
        self.L_SHOULDER = 11
        self.R_SHOULDER = 12
        self.L_ELBOW = 13
        self.R_ELBOW = 14
        self.L_WRIST = 15
        self.R_WRIST = 16
        self.L_HIP = 23
        self.R_HIP = 24

    def update_config(self, new_config: Dict[str, Any]):
        """Dynamically updates solver heuristics."""
        self.config.update(new_config)
        print(f"[JointMapper] Config Updated: {self.config}")

    def map_to_robot(self, human: HumanSkeleton) -> Dict[str, float]:
        """
        Standardized mapping with Exponential Smoothing (Low-Pass Filter).
        """
        raw_angles = {}
        
        if not human or not hasattr(human, 'joints'):
            return self._get_neutral_state()

        # --- COORDINATE MAPPING LOGIC ---
        
        # 1. Left Arm
        l_elbow_pitch = np.degrees(human.get_angle(11, 13, 15))
        raw_angles["l_elbow_pitch"] = self.robot.clamp("elbow_pitch", l_elbow_pitch)

        l_upper_arm_v = human.get_vector(11, 13)
        l_shoulder_pitch = self._safe_pitch(l_upper_arm_v, "l_shoulder_pitch")
        raw_angles["l_shoulder_pitch"] = self.robot.clamp("shoulder_pitch", l_shoulder_pitch)

        # 2. Right Arm
        r_elbow_pitch = np.degrees(human.get_angle(12, 14, 16))
        raw_angles["r_elbow_pitch"] = self.robot.clamp("elbow_pitch", r_elbow_pitch)

        r_upper_arm_v = human.get_vector(12, 14)
        r_shoulder_pitch = self._safe_pitch(r_upper_arm_v, "r_shoulder_pitch")
        raw_angles["r_shoulder_pitch"] = self.robot.clamp("shoulder_pitch", r_shoulder_pitch)

        # 3. Torso
        shoulder_vector = human.get_vector(11, 12)
        hip_vector = human.get_vector(23, 24)
        if np.linalg.norm(shoulder_vector) < 1e-6 or np.linalg.norm(hip_vector) < 1e-6:
            waist_yaw = self.last_angles.get("waist_yaw", 0.0)
        else:
            waist_yaw = np.degrees(np.arctan2(shoulder_vector[0], shoulder_vector[2]) -
                                   np.arctan2(hip_vector[0], hip_vector[2]))
        raw_angles["waist_yaw"] = self.robot.clamp("waist_yaw", waist_yaw)

        # --- HEURISTICS & SMOOTHING ---
        alpha = 1.0 - self.config["smoothing_factor"]
        smoothed_angles = {}
        
        for joint, angle in raw_angles.items():
            last_angle = self.last_angles.get(joint, angle)
            # EMA: current = (1-a)*prev + a*current
            smoothed = (1 - alpha) * last_angle + alpha * angle
            smoothed_angles[joint] = smoothed
            self.last_angles[joint] = smoothed

        smoothed_angles["timestamp"] = time.time()
        smoothed_angles["status"] = "SOLVER_STABLE"
        return smoothed_angles

    def _safe_pitch(self, vector: np.ndarray, joint_name: str) -> float:
        if np.linalg.norm(vector) < 1e-6:
            return self.last_angles.get(joint_name, 0.0)
        return float(np.degrees(np.arctan2(vector[1], vector[2] + 1e-6)))

    def _get_neutral_state(self) -> Dict[str, Any]:
        return {
            "l_shoulder_pitch": 0.0,
            "l_elbow_pitch": 0.0,
            "r_shoulder_pitch": 0.0,
            "r_elbow_pitch": 0.0,
            "waist_yaw": 0.0,
            "timestamp": time.time(),
            "status": "NEUTRAL_FALLBACK"
        }

    def reset(self):
        self.last_angles.clear()
