from typing import Dict, Tuple

class UniversalHumanoidModel:
    """
    Standardized Kinematic Model for Universal Humanoid Control.
    Defines DOF (Degrees of Freedom) and Joint Limits common to major humanoid platforms.
    """
    def __init__(self):
        # Universal Joint Limits (Degrees)
        self.limits = {
            # Upper Body
            "shoulder_pitch": (-180, 90),
            "shoulder_roll": (-90, 10),
            "elbow_yaw": (-90, 90),
            "elbow_pitch": (0, 150),
            "wrist_pitch": (-90, 90),
            "wrist_roll": (-45, 45),
            
            # Torso
            "waist_yaw": (-90, 90),
            "waist_pitch": (-30, 90),
            
            # Lower Body
            "hip_pitch": (-90, 30),
            "hip_roll": (-20, 20),
            "knee_pitch": (0, 150),
            "ankle_pitch": (-45, 45),
            "ankle_roll": (-20, 20)
        }

    def clamp(self, joint_name: str, angle_deg: float) -> float:
        """Enforces physical constraints on joint movements."""
        if joint_name not in self.limits:
            return angle_deg
        
        lower, upper = self.limits[joint_name]
        return max(min(angle_deg, upper), lower)

    def get_dof_config(self) -> Dict[str, Tuple[float, float]]:
        """Returns the full DOF configuration for external simulation/hardware."""
        return self.limits
