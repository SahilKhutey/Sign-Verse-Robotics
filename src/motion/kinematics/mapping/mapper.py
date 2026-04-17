import numpy as np
from typing import Dict
from src.motion.kinematics.models.human import HumanSkeleton
from src.motion.kinematics.models.robot import UniversalHumanoidModel

class JointMapper:
    """
    Kinematic Mapping Engine.
    Maps 3D human landmark geometry to standardized robotic JointState.
    """
    def __init__(self, robot_model: UniversalHumanoidModel):
        self.robot = robot_model
        
        # Landmark Indices (MediaPipe Holistic/Pose)
        self.L_SHOULDER = 11
        self.R_SHOULDER = 12
        self.L_ELBOW = 13
        self.R_ELBOW = 14
        self.L_WRIST = 15
        self.R_WRIST = 16
        self.L_HIP = 23
        self.R_HIP = 24
        self.L_KNEE = 25
        self.R_KNEE = 26
        self.L_ANKLE = 27
        self.R_ANKLE = 28

    def map_to_robot(self, human: HumanSkeleton) -> Dict[str, float]:
        """
        Calculates joint angles for a full humanoid robot based on human observations.
        Returns angles in Degrees, clamped to robot limits.
        """
        joint_angles = {}

        # 1. Arm Kinematics (Left Example)
        # Elbow Pitch: Angle at Elbow (13) between Shoulder (11) and Wrist (15)
        l_elbow_pitch = np.degrees(human.get_angle(11, 13, 15))
        joint_angles["l_elbow_pitch"] = self.robot.clamp("elbow_pitch", l_elbow_pitch)

        # Shoulder Pitch: Vertical angle of the upper arm
        # Simplified vector-based mapping
        l_upper_arm_v = human.get_vector(11, 13)
        l_shoulder_pitch = np.degrees(np.arctan2(l_upper_arm_v[1], l_upper_arm_v[2]))
        joint_angles["l_shoulder_pitch"] = self.robot.clamp("shoulder_pitch", l_shoulder_pitch)

        # 2. Torso Kinematics
        # Waist Yaw: Rotation of the shoulders relative to the hips (simplified)
        shoulder_vector = human.get_vector(11, 12)
        hip_vector = human.get_vector(23, 24)
        waist_yaw = np.degrees(np.arctan2(shoulder_vector[0], shoulder_vector[2]) - 
                               np.arctan2(hip_vector[0], hip_vector[2]))
        joint_angles["waist_yaw"] = self.robot.clamp("waist_yaw", waist_yaw)

        # 3. Leg Kinematics (Left Example)
        l_knee_pitch = np.degrees(human.get_angle(23, 25, 27))
        joint_angles["l_knee_pitch"] = self.robot.clamp("knee_pitch", l_knee_pitch)

        return joint_angles
