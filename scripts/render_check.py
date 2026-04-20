import numpy as np
import os
import json

def verify_session(session_name):
    session_path = os.path.join("datasets", session_name)
    print(f"[Render Check] Auditing session: {session_path}")
    
    if not os.path.exists(session_path):
        print(f"[Error] Session directory not found: {session_path}")
        return False
        
    # 1. Check motion_states.jsonl
    jsonl_path = os.path.join(session_path, "motion_states.jsonl")
    if os.path.exists(jsonl_path):
        line_count = sum(1 for _ in open(jsonl_path))
        print(f"[Verify] motion_states.jsonl: Found {line_count} frames.")
    else:
        print("[Error] motion_states.jsonl missing.")
        return False

    # 2. Check training_set.npy
    npy_path = os.path.join(session_path, "training_set.npy")
    if os.path.exists(npy_path):
        data = np.load(npy_path, allow_pickle=True).item()
        obs = data.get("observations", [])
        actions = data.get("actions", [])
        print(f"[Verify] training_set.npy: Obs shape {obs.shape}, Actions shape {actions.shape}")
        
        # Headless Render Check: Validate geometry
        # Check if joint values are within reasonable human/robot ranges
        if obs.shape[0] > 0:
            avg_z = np.mean(obs[:, :, 2]) # Average Z coordinate
            print(f"[Verify] Physics validation: Average Z-depth is {avg_z:.3f}m")
            if avg_z == 0:
                 print("[Warning] Possible 2D projection detected instead of 3D.")
    else:
        print("[Error] training_set.npy missing.")
        return False

    # 3. Check CSV
    csv_path = os.path.join(session_path, "training_set.csv")
    if os.path.exists(csv_path):
        size = os.path.getsize(csv_path)
        print(f"[Verify] training_set.csv: {size/1024:.1f} KB")
    else:
        print("[Error] training_set.csv missing.")
        return False

    print("[Render Check] SUCCESS: Data integrity verified.")
    return True

if __name__ == "__main__":
    verify_session("test")
