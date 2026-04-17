import os
import subprocess
from typing import List, Dict, Any

class BlenderBridge:
    """
    Blender Bridge for complex operations like FBX export and render automation.
    Uses headless Blender CLI to avoid heavy binary dependencies.
    """
    def __init__(self, blender_path: str = "blender"):
        self.blender_path = blender_path

    def export_fbx(self, 
                   source_blend: str, 
                   export_path: str, 
                   animation_data: List[Dict[str, Any]]):
        """
        Generates a 1-time script to apply animation data and export as FBX.
        """
        script_content = f"""
import bpy
import json

# Setup scene
bpy.ops.wm.open_mainfile(filepath='{source_blend}')
arm = bpy.data.objects.get('Armature')

# Apply Animation (simplified for bridge)
animation_data = {json.dumps(animation_data)}

for frame_idx, pose in enumerate(animation_data):
    bpy.context.scene.frame_set(frame_idx)
    for bone_name, rotation in pose.items():
        bone = arm.pose.bones.get(bone_name)
        if bone:
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = rotation
            bone.keyframe_insert(data_path='rotation_euler')

# Export FBX
bpy.ops.export_scene.fbx(filepath='{export_path}', use_selection=True)
"""
        script_path = "temp_fbx_export.py"
        with open(script_path, "w") as f:
            f.write(script_content)
            
        # Execute Headless Blender
        try:
            subprocess.run([
                self.blender_path, "--background", "--python", script_path
            ], check=True)
            print(f"✅ FBX Export Successful: {export_path}")
        except Exception as e:
            print(f"❌ FBX Export Failed: {e}")
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
