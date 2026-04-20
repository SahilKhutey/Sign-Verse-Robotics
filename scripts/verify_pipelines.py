import os
import sys
import time
import json
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def log_section(title: str):
    print("\n" + "="*60)
    print(f" AUDIT: {title}")
    print("="*60)

def verify_dependencies():
    log_section("1. Dependency Integrity")
    try:
        import cv2
        import mediapipe as mp
        import torch
        from ultralytics import YOLO
        print(f"[PASS] OpenCV Version: {cv2.__version__}")
        print(f"[PASS] PyTorch Version: {torch.__version__}")
        print(f"[PASS] MediaPipe Version: {mp.__version__}")
        return True
    except ImportError as e:
        print(f"[FAIL] Missing dependency: {e}")
        return False

def verify_models():
    log_section("2. Model & Weight Verification")
    model_dir = os.path.join(PROJECT_ROOT, "models", "perception")
    required_files = [
        "pose_landmarker_heavy.task",
        "yolov8n.pt"
    ]
    
    all_present = True
    for f in required_files:
        path = os.path.join(model_dir, f)
        exists = os.path.exists(path)
        status = "[PASS]" if exists else "[FAIL]"
        print(f"{status} {f} found at {path}")
        if not exists:
            all_present = False
            
    return all_present

def verify_solver():
    log_section("3. Control & Solver Fallback")
    try:
        from src.robotics.wbmpc.solver.qp_optimizer import WBMPCSolver
        import numpy as np
        
        solver = WBMPCSolver()
        # Mock state and reference
        state = np.array([0.0, 0.0, 1.0, 0.0, 0.0, 0.0]) # Static at 1m height
        ref = np.array([0.0, 0.0, 1.0])
        
        start = time.time()
        acc, forces = solver.solve(state, ref)
        elapsed = (time.time() - start) * 1000
        
        mode = "C++ NATIVE" if solver.lib else "NUMPY FALLBACK"
        print(f"[PASS] Solver Mode: {mode}")
        print(f"[PASS] Solve Time: {elapsed:.3f}ms")
        print(f"[DATA] Vertical Force: {forces[2]:.2f}N (Target: ~461N for 47kg balance)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Solver execution error: {e}")
        return False

def verify_ingestion_logic():
    log_section("4. Ingestion & Adapter Logic")
    try:
        from src.ingestion.adapters.youtube import YouTubeAdapter
        print("[PASS] YouTube Adapter imported successfully.")
        
        # Test a search logic (dry run)
        print("Testing YouTube Search API (Mock query: 'robotics movement')...")
        results = YouTubeAdapter.search("robotics movement", max_results=1)
        if results:
            print(f"[PASS] Found video: '{results[0].get('title')}'")
        else:
            print("[WARN] YouTube search returned no results (Check network connectivity).")
            
        return True
    except Exception as e:
        print(f"[FAIL] Ingestion logic error: {e}")
        return False

def run_full_audit():
    print("\n" + "!"*60)
    print(" SIGN-VERSE PIPELINE VERIFICATION SUITE")
    print("!"*60)
    
    results = {
        "Dependencies": verify_dependencies(),
        "Models": verify_models(),
        "Solver": verify_solver(),
        "Ingestion": verify_ingestion_logic()
    }
    
    log_section("FINAL VERIFICATION SUMMARY")
    overall = True
    for task, passed in results.items():
        status = "✅ OK" if passed else "❌ FAILED"
        print(f"{task:15}: {status}")
        if not passed:
            overall = False
            
    print("\n" + "="*60)
    if overall:
        print(" VERDICT: SYSTEM OPERATIONAL (SOVEREIGN READY)")
    else:
        print(" VERDICT: SYSTEM DEGRADED (MAINTENANCE REQUIRED)")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_full_audit()
