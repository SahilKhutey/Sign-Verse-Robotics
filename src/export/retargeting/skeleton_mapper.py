from typing import Dict, Any, List

class SkeletonMapper:
    """
    Retargets internal joint states to target industry-standard rigs.
    Handles coordinate space translation and nomenclature mapping.
    """
    def __init__(self, target_rig: str = "mixamo"):
        self.target_rig = target_rig
        
        # Mapping Configuration
        self.MAPS = {
            "mixamo": {
                "pelvis": "mixamorig:Hips",
                "spine_mid": "mixamorig:Spine",
                "neck": "mixamorig:Neck",
                "shoulder_left": "mixamorig:LeftArm",
                "elbow_left": "mixamorig:LeftForeArm",
                "wrist_left": "mixamorig:LeftHand",
                "shoulder_right": "mixamorig:RightArm",
                "elbow_right": "mixamorig:RightForeArm",
                "wrist_right": "mixamorig:RightHand",
                "hip_left": "mixamorig:LeftUpLeg",
                "knee_left": "mixamorig:LeftLeg",
                "ankle_left": "mixamorig:LeftFoot",
                "hip_right": "mixamorig:RightUpLeg",
                "knee_right": "mixamorig:RightLeg",
                "ankle_right": "mixamorig:RightFoot"
            },
            "ue5": {
                "pelvis": "pelvis",
                "spine_mid": "spine_01",
                "neck": "neck_01",
                "shoulder_left": "upperarm_l",
                "elbow_left": "lowerarm_l",
                "wrist_left": "hand_l",
                "shoulder_right": "upperarm_r",
                "elbow_right": "lowerarm_r",
                "wrist_right": "hand_r"
            }
        }

    def retarget(self, joint_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the internal joint data keys to the target rig's bone names.
        """
        target_map = self.MAPS.get(self.target_rig, {})
        mapped_data = {}
        
        for internal_key, value in joint_state.items():
            if internal_key in target_map:
                mapped_data[target_map[internal_key]] = value
            else:
                # Pass through unmapped data (e.g. root transform)
                mapped_data[internal_key] = value
                
        return mapped_data
