from typing import Dict, Any, List, Optional

class RetargetEngine:
    """
    Industry-grade Retargeting Engine for Human-to-Robot mapping.
    Maps MediaPipe/Internal landmarks to URDF/Rig link names.
    Includes built-in 'Humanoid' profile.
    """
    def __init__(self, target_profile: str = "humanoid"):
        self.profile = target_profile
        
        # Mapping: {Internal_Joint: Robot_Link}
        self.PROFILES = {
            "humanoid": {
                "shoulder_left": "left_upper_arm",
                "elbow_left": "left_lower_arm",
                "wrist_left": "left_hand",
                "shoulder_right": "right_upper_arm",
                "elbow_right": "right_lower_arm",
                "wrist_right": "right_hand",
                "hip_left": "left_thigh",
                "knee_left": "left_calf",
                "ankle_left": "left_foot"
            }
        }

    def retarget(self, joint_state: Dict[str, Any], custom_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Translates a human skeletal state into a robot-link-aligned state.
        Uses the selected profile or a provided custom mapping (Any Robot).
        """
        mapping = custom_mapping if custom_mapping else self.PROFILES.get(self.profile, {})
        retargeted_state = {}
        
        for human_joint, robot_link in mapping.items():
            if human_joint in joint_state:
                # Direct coordinate/rotation transfer or modulation
                retargeted_state[robot_link] = joint_state[human_joint]
            else:
                # Default to identity if landmark is missing
                retargeted_state[robot_link] = [0, 0, 0]
                
        return retargeted_state
