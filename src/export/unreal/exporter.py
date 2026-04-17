import json
from typing import Dict, Any

class UnrealExporter:
    """
    Exports joint states and transforms to Unreal Engine 5.
    Implements coordinate-space conversion from internal (Y-up, RH) to UE5 (Z-up, LH).
    """
    def __init__(self, scale_factor: float = 100.0):
        self.scale = scale_factor

    def convert_to_ue5(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts internal right-handed Y-up coordinates to UE5's left-handed Z-up space.
        RH [x, y, z] -> LH [x, z, y] (approximate world-space flip)
        """
        if isinstance(value, list) and len(value) == 3:
            # Position conversion
            return [value[0] * self.scale, value[2] * self.scale, value[1] * self.scale]
        
        if isinstance(value, dict) and "x" in value:
            # Quaternion or Euler dict conversion
            return {
                "x": value["x"],
                "y": -value["z"], # Handedness flip
                "z": value["y"]
            }
        return value

    def to_json_payload(self, mapped_joint_data: Dict[str, Any]) -> str:
        """
        Formats the data into a JSON string for WebSocket/LiveLink ingestion.
        """
        ue5_data = {}
        for bone, state in mapped_joint_data.items():
            ue5_data[bone] = self.convert_to_ue5(state)
            
        return json.dumps({
            "type": "pose_update",
            "coordinate_space": "LH_Z_UP",
            "bones": ue5_data
        })
