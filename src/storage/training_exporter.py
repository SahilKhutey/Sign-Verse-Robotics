import json
import os
import numpy as np
import pandas as pd
from typing import List, Dict
from src.motion.kinematics.mapping.mapper import JointMapper
from src.motion.kinematics.models.robot import UniversalHumanoidModel
from src.motion.kinematics.models.human import HumanSkeleton

class TrainingExporter:
    """
    Sign-Verse Training Data Factory.
    Converts raw Human performance logs into synchronized Robot Joint datasets.
    Supports .npy (Tensors) and .csv (Analytics).
    """
    def __init__(self):
        self.model = UniversalHumanoidModel()
        self.mapper = JointMapper(self.model)

    def process_session(self, session_dir: str, export_name: str = "training_set"):
        """
        Batch processes a recorded session into training pairs.
        """
        input_file = os.path.join(session_dir, "motion_states.jsonl")
        if not os.path.exists(input_file):
            print(f"[Exporter Error] Session file not found: {input_file}")
            return False

        print(f"[Exporter] Processing session: {session_dir}")
        
        human_data = []
        robot_data = []
        timestamps = []

        # Buffer results to avoid massive list growing, but maintain order
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if "joints" not in entry or entry["joints"] is None:
                        continue

                    # 1. Reconstruct Human Skeleton
                    # Use numpy only for the specific frame processing
                    skeleton_arr = np.array(entry["joints"])
                    skeleton = HumanSkeleton(skeleton_arr)
                    
                    # 2. Map to Robot Joints
                    joint_angles = self.mapper.map_to_robot(skeleton)
                    
                    # 3. Collect Data
                    human_data.append(entry["joints"])
                    # Exclude non-kineamtic keys
                    action_vector = [val for key, val in joint_angles.items() if key not in ["timestamp", "status"]]
                    robot_data.append(action_vector)
                    timestamps.append(entry.get("timestamp", 0.0))
                except Exception as e:
                    print(f"[Exporter] Skipping corrupted frame: {e}")
                    continue

        if not human_data:
            print("[Exporter Warning] No valid motion frames found in session.")
            return False

        # Convert to final arrays for saving
        # Optimization: cast to float32 to save disk/memory
        human_arr = np.array(human_data, dtype=np.float32)
        robot_arr = np.array(robot_data, dtype=np.float32)
        
        # --- EXPORT 1: NPY (High Speed ML) ---
        target_path_npy = os.path.join(session_dir, f"{export_name}.npy")
        np.save(target_path_npy, {
            "observations": human_arr,
            "actions": robot_arr,
            "timestamps": np.array(timestamps)
        })
        print(f"[Exporter] Successfully generated .npy: {target_path_npy}")

        # --- EXPORT 2: CSV (Analytics & Human Readable) ---
        target_path_csv = os.path.join(session_dir, f"{export_name}.csv")
        
        # Flatten joint columns for CSV
        df_cols = [f"human_j{i}_{axis}" for i in range(human_arr.shape[1]) for axis in ['x', 'y', 'z']]
        # Actually, let's just use joint names if we have them, otherwise indices
        
        # Create a cleaner DataFrame
        df = pd.DataFrame(robot_arr, columns=list(joint_angles.keys())[:-2])
        df['timestamp'] = timestamps
        df.to_csv(target_path_csv, index=False)
        print(f"[Exporter] Successfully generated .csv: {target_path_csv}")

        return True

if __name__ == "__main__":
    # Test stub
    exporter = TrainingExporter()
    # exporter.process_session("data/sessions/session_xyz")
