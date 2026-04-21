import requests
import time
import sys
import os

# Configuration for the 50-video wave
CATEGORIES = ["workout", "dance", "sports", "arts", "cooking", "acting", "parkour", "martial arts", "yoga", "speech"]
RESULTS_PER_CATEGORY = 5
SAMPLE_FPS = 2.0
CHUNK_FRAMES = 100
API_BASE = "http://localhost:8000"

def schedule_wave():
    print(f"!!! SIGN-VERSE OVERNIGHT WAVE SCHEDULER !!!")
    print(f"Target: {len(CATEGORIES) * RESULTS_PER_CATEGORY} videos across {len(CATEGORIES)} categories.")
    
    while True:
        try:
            # Check current status
            res = requests.get(f"{API_BASE}/pipeline/youtube/auto/status")
            if res.status_code == 200:
                data = res.json()
                status = data.get("status")
                job = data.get("job")
                
                if status == "idle" or (job and job.get("status") in ["completed", "failed", "interrupted", "error"]):
                    print("[INFO] No job currently running. Initiating 50-video wave...")
                    
                    # Start the new job
                    payload = {
                        "categories": CATEGORIES,
                        "results_per_category": RESULTS_PER_CATEGORY,
                        "sample_fps": SAMPLE_FPS,
                        "chunk_frames": CHUNK_FRAMES
                    }
                    
                    start_res = requests.post(f"{API_BASE}/pipeline/youtube/auto/start", json=payload)
                    if start_res.status_code == 200:
                        start_data = start_res.json()
                        print(f"[SUCCESS] Overnight wave started: {start_data['job']['job_id']}")
                        break
                    else:
                        print(f"[ERROR] Failed to start wave: {start_res.text}")
                        # If it failed because another job started in the split second, we loop back
                else:
                    print(f"[WAIT] Active job detected ({job.get('job_id')}). Retrying in 60s...")
            else:
                print(f"[ERROR] Backend unreachable: {res.status_code}. Retrying in 10s...")
                
        except Exception as e:
            print(f"[ERROR] Connection error: {e}. Retrying in 10s...")
            
        time.sleep(60)

if __name__ == "__main__":
    schedule_wave()
