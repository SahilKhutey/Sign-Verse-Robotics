
import bpy
import os
import sys

# Add our scripts dir to path
sys.path.append(r"C:\Users\User\Documents\Sign-Verse-Robotics\scripts\blender")

# Create basic armature if file is empty/new
if not bpy.data.objects:
    bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
    bpy.context.object.name = "SignVerse_Armature"

# Execute the live-link addon
try:
    with open(r"C:\Users\User\Documents\Sign-Verse-Robotics\scripts\blender\sign_verse_addon.py", "r") as f:
        exec(f.read())
    print("[Sign-Verse] Bridge script initialized successfully.")
except Exception as e:
    print(f"[Sign-Verse] Bridge error: {e}")

# Save the project file
if not os.path.exists(r"C:\Users\User\Documents\Sign-Verse-Robotics\data\simulation\sign_verse_sim.blend"):
    bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\User\Documents\Sign-Verse-Robotics\data\simulation\sign_verse_sim.blend")
