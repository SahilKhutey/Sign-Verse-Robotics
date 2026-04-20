import os
import sys
import time
from typing import List

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.auto_youtube_pipeline import AutoYouTubePipelineManager

CATEGORIES = [
    "workout", "art", "cooking", "speech", "sports", 
    "acting", "dance", "parkour", "martial arts", "yoga"
]

def run_test2_batch():
    print("\n" + "!"*60)
    print(" SIGN-VERSE BATCH SYNTHESIS: TEST2 (10 CATEGORIES)")
    print("!"*60)
    
    manager = AutoYouTubePipelineManager()
    
    # We set results_per_category to 1 to get exactly 10 videos.
    # We set sample_fps to 30.0 for "Real Time" fidelity as requested.
    job_params = {
        "categories": CATEGORIES,
        "results_per_category": 1,
        "sample_fps": 30.0,
        "chunk_frames": 100
    }
    
    print(f"Initializing job with parameters: {job_params}")
    
    try:
        job = manager.start_job(**job_params)
        job_id = job["job_id"]
        print(f"\n[SUCCESS] Job {job_id} started in the background.")
        print(f"Monitoring progress...")
        
        while True:
            status = manager.get_job(job_id)
            if status["status"] in ["completed", "error", "interrupted"]:
                break
            
            print(f"[{time.strftime('%H:%M:%S')}] Phase: {status['phase']:15} | {status['message']}")
            time.sleep(10)
            
        final_status = manager.get_job(job_id)
        if final_status["status"] == "completed":
            print("\n" + "="*60)
            print(" BATCH SYNTHESIS COMPLETE")
            print("="*60)
            print(f"Batch ID: {final_status['batch_id']}")
            print(f"Batch Directory: {final_status['batch_dir']}")
            print(f"Videos Processed: {len(final_status['downloaded_videos'])}")
            print("="*60 + "\n")
        else:
            print(f"\n[ERROR] Job failed: {final_status.get('error')}")
            
    except Exception as e:
        print(f"[FATAL] Failed to start job: {e}")

if __name__ == "__main__":
    run_test2_batch()
