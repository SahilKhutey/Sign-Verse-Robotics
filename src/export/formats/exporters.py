import json
from typing import List, Dict, Any

class BVHExporter:
    """
    Exports motion sequences to the Biovision Hierarchy (BVH) format.
    """
    def export(self, hierarchy_spec: Dict[str, Any], motion_data: List[List[float]], filepath: str):
        with open(filepath, "w") as f:
            f.write("HIERARCHY\n")
            # Recursive hierarchy writing would go here
            f.write("ROOT Hips\n{\n  OFFSET 0.00 0.00 0.00\n  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n  End Site\n  {\n    OFFSET 0.00 0.00 0.00\n  }\n}\n")
            
            f.write(f"MOTION\nFrames: {len(motion_data)}\nFrame Time: 0.033333\n")
            for frame in motion_data:
                line = " ".join(f"{val:.6f}" for val in frame)
                f.write(line + "\n")
        print(f"✅ BVH Exported to {filepath}")

class GLTFExporter:
    """
    Exports animation data for Web/XR via GLTF JSON structures.
    """
    def export_to_json(self, animation_sequence: List[Dict[str, Any]]) -> str:
        return json.dumps({
            "asset": {"version": "2.0", "generator": "Sign-Verse REL"},
            "animations": [{
                "name": "SignLanguage_Sequence",
                "tracks": animation_sequence
            }]
        })
