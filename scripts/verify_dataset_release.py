import os
import json
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTION_BASE = os.path.join(PROJECT_ROOT, "datasets", "production", "sign_verse_v1")
INDEX_PATH = os.path.join(PRODUCTION_BASE, "index.json")

def verify_and_check_sizes():
    if not os.path.exists(INDEX_PATH):
        print(f"ERROR: Index not found at {INDEX_PATH}")
        return

    with open(INDEX_PATH, "r") as f:
        index = json.load(f)

    print(f"--- Verifying {index['dataset_name']} ---")
    
    all_ok = True
    large_files = []

    for vid in index["videos"]:
        print(f"Checking Video: {vid['slug']}")
        for key, rel_path in vid["files"].items():
            abs_path = os.path.join(PRODUCTION_BASE, rel_path)
            
            if not os.path.exists(abs_path):
                print(f"  [MISSING] {key}: {rel_path}")
                all_ok = False
                continue

            size_mb = os.path.getsize(abs_path) / (1024 * 1024)
            if size_mb > 50:
                large_files.append((rel_path, size_mb))

            # Sample validation for NPY
            if key == "training_set_npy":
                try:
                    data = np.load(abs_path, allow_pickle=True)
                    # print(f"    NPY Shape: {data.shape}")
                except Exception as e:
                    print(f"    [CORRUPT] NPY {rel_path}: {e}")
                    all_ok = False

    print("\n--- Summary ---")
    if all_ok:
        print("Integrity: PASSED")
    else:
        print("Integrity: FAILED")

    if large_files:
        print("\nLarge Files (>50MB):")
        for path, size in large_files:
            print(f"  {path}: {size:.2f} MB")
    else:
        print("\nNo files > 50MB found. Git push should be safe.")

if __name__ == "__main__":
    verify_and_check_sizes()
