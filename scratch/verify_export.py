import os
import json
import numpy as np
from src.storage.training_exporter import TrainingExporter

# Create a mock session for verification
os.makedirs("datasets/test_session", exist_ok=True)
mock_file = "datasets/test_session/motion_states.jsonl"

with open(mock_file, "w") as f:
    for i in range(10):
        # 33 landmarks for MediaPipe Pose
        joints = np.random.rand(33, 3).tolist()
        entry = {
            "timestamp": 12345.67 + i * 0.03,
            "position": [0.1, 0.2, 0.3],
            "velocity": [0.0, 0.0, 0.0],
            "confidence": 0.9,
            "joints": joints
        }
        f.write(json.dumps(entry) + "\n")

print("[Test] Mock session created. Running exporter...")

exporter = TrainingExporter()
success = exporter.process_session("datasets/test_session", export_name="verified_training")

if success:
    print("[Test] SUCCESS: Export generated.")
    if os.path.exists("datasets/test_session/verified_training.npy"):
        print("[Test] SUCCESS: .npy file found.")
    if os.path.exists("datasets/test_session/verified_training.csv"):
        print("[Test] SUCCESS: .csv file found.")
else:
    print("[Test] FAILED: Exporter returned error.")
