import os
import sys
import time
import torch
import numpy as np
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)

def analyze_perception_models():
    print("\n" + "="*60)
    print(" PERCEPTION MODEL AUDIT (MediaPipe/YOLO)")
    print("="*60)
    
    perception_root = os.path.join(PROJECT_ROOT, "models", "perception")
    models = [
        "face_landmarker.task",
        "hand_landmarker.task",
        "pose_landmarker_lite.task",
        "pose_landmarker_full.task",
        "pose_landmarker_heavy.task",
        "yolov8n.pt"
    ]
    
    for model_name in models:
        path = os.path.join(perception_root, model_name)
        if os.path.exists(path):
            size = get_file_size_mb(path)
            print(f"| {model_name:<30} | {size:>8.2f} MB |")
        else:
            print(f"| {model_name:<30} | {'MISSING':>11} |")

def analyze_mmte_model():
    print("\n" + "="*60)
    print(" COGNITIVE MODEL AUDIT (MMTE/TIE)")
    print("="*60)
    
    mmte_path = os.path.join(PROJECT_ROOT, "models", "mmte", "checkpoints", "latest.pt")
    if not os.path.exists(mmte_path):
        print("[ERROR] MMTE checkpoint not found.")
        return

    size = get_file_size_mb(mmte_path)
    print(f"Model Path: {mmte_path}")
    print(f"Storage Size: {size:.2f} MB")
    
    try:
        # Load model to CPU for analysis
        checkpoint = torch.load(mmte_path, map_location="cpu", weights_only=True)
        
        # If it's a state dict or a wrapped model
        if isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint.state_dict() if hasattr(checkpoint, "state_dict") else None

        if state_dict:
            params = sum(p.numel() for p in state_dict.values())
            print(f"Parameter Count: {params/1e6:.2f}M")
            
            # Benchmark inference latency (MOCK INPUT)
            # Assuming MMTE input is (batch, seq, features) = (1, 64, 345) based on docs
            input_tensor = torch.randn(1, 64, 345)
            
            # We would need the actual model class to trace/benchmark properly
            # For now, we report the footprint
            print(f"Memory Footprint (Weights): ~{size:.2f} MB")
        else:
            print("[WARNING] Could not extract state_dict for parameter count.")
            
    except Exception as e:
        print(f"[ERROR] Could not analyze MMTE weights: {e}")

def main():
    print("!!! SIGN-VERSE MODEL FOOTPRINT ANALYSIS !!!")
    analyze_perception_models()
    analyze_mmte_model()
    
    print("\n" + "="*60)
    print(" PRUNING RECOMMENDATIONS")
    print("="*60)
    print("1. [PERCEPTION] Use 'lite' pose landmarker (5.7MB) instead of 'heavy' (30.6MB) for OAK-D.")
    print("2. [MMTE] Apply INT8 Dynamic Quantization to reducing weights from 13.7MB to ~4MB.")
    print("3. [YOLO] Export YOLOv8n specifically to OpenVINO or TensorRT for hardware acceleration.")
    print("="*60)

if __name__ == "__main__":
    main()
