import subprocess
import os
import sys
import time

def launch_blender_simulator(blender_path: str = None, project_name: str = "sign_verse_sim.blend"):
    """
    Automates the creation and launch of the Sign-Verse Blender Simulation.
    Creates a basic project file and injects the live-link bridge script.
    """
    # 1. Resolve Blender Path
    if not blender_path:
        # Common installation paths on Windows
        search_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender-launcher.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        ]
        for p in search_paths:
            if os.path.exists(p):
                blender_path = p
                break
    
    if not blender_path:
        print("[Error] Blender executable not found. Please provide the path manually.")
        return

    # 2. Path to project and addon
    script_dir = os.path.dirname(os.path.abspath(__file__))
    addon_path = os.path.join(script_dir, "sign_verse_addon.py")
    project_path = os.path.join(os.getcwd(), "data", "simulation", project_name)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(project_path), exist_ok=True)

    print(f"[Launcher] Found Blender at: {blender_path}")
    print(f"[Launcher] Auto-Creating Project: {project_path}")

    # 3. Bootstrap Script
    # This script will run inside Blender to initialize the armature and start the bridge
    bootstrap_script = f"""
import bpy
import os
import sys

# Add our scripts dir to path
sys.path.append(r"{script_dir}")

# Create basic armature if file is empty/new
if not bpy.data.objects:
    bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
    bpy.context.object.name = "SignVerse_Armature"

# Execute the live-link addon
try:
    with open(r"{addon_path}", "r") as f:
        exec(f.read())
    print("[Sign-Verse] Bridge script initialized successfully.")
except Exception as e:
    print(f"[Sign-Verse] Bridge error: {{e}}")

# Save the project file
if not os.path.exists(r"{project_path}"):
    bpy.ops.wm.save_as_mainfile(filepath=r"{project_path}")
"""

    bootstrap_path = os.path.join(script_dir, "bootstrap_sim.py")
    with open(bootstrap_path, "w") as f:
        f.write(bootstrap_script)

    # 4. Launch Blender
    cmd = [
        blender_path,
        "-y", # Enable automatic Python execution
        "--python", bootstrap_path
    ]

    print(f"[Launcher] Launching Blender Workshop...")
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

if __name__ == "__main__":
    launch_blender_simulator()
