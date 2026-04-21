import os
import sys
import time
import json
import traceback
from hashlib import sha1

# Setup pathing
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ingestion.adapters.youtube import YouTubeAdapter
from scripts.run_video_workflow import run_workflow
from scripts.render_check import verify_session

# CONFIGURATION
CATEGORIES = [
    "workout", "dance", "sports", "arts", "cooking", 
    "acting", "parkour", "martial arts", "yoga", "speech"
]
TARGET_PER_CATEGORY = 5
SAMPLE_FPS = 2.0
CHUNK_FRAMES = 100
WAVE_ID = "final_bulletproof_wave_20260421"
WAVE_DIR = os.path.join(PROJECT_ROOT, "datasets", "auto_jobs", WAVE_ID)
DOWNLOAD_DIR = os.path.join(WAVE_DIR, "downloads")
LOG_FILE = os.path.join(WAVE_DIR, "wave_execution.log")

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def execute_wave():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    log(f"Starting Mission-Critical Wave: {WAVE_ID}")
    
    manifest_path = os.path.join(WAVE_DIR, "wave_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    else:
        manifest = {"wave_id": WAVE_ID, "completed_videos": []}

    processed_urls = {v["url"] for v in manifest["completed_videos"]}

    for index, category in enumerate(CATEGORIES, start=1):
        log(f"Processing Category ({index}/{len(CATEGORIES)}): {category}")
        
        query = f"{category} performance tutorial movement"
        # Search for a healthy buffer
        candidates = YouTubeAdapter.search(query, max_results=20)
        
        successful_in_category = 0
        # Check how many we already have for this category in the manifest
        successful_in_category = len([v for v in manifest["completed_videos"] if v.get("category") == category])
        
        log(f"Currently have {successful_in_category}/{TARGET_PER_CATEGORY} for {category}")

        for cand in candidates:
            if successful_in_category >= TARGET_PER_CATEGORY:
                break
                
            url = cand["url"]
            if url in processed_urls:
                continue

            log(f"Attempting Video: {cand['title']} ({url})")
            
            try:
                # 1. DOWNLOAD
                prefix = f"{index:02d}_{category}"
                download_info = YouTubeAdapter.download_video(
                    url, 
                    DOWNLOAD_DIR, 
                    filename_prefix=prefix
                )
                
                if not download_info or not os.path.exists(download_info["local_path"]):
                    log(f"Download failed or returned None for {url}. Skipping.")
                    continue

                # 2. PERCEPTION WORKFLOW
                base_name = os.path.basename(download_info["local_path"])
                session_id = f"{WAVE_ID}_{prefix}_{sha1(url.encode()).hexdigest()[:6]}"
                
                log(f"Starting Perception for {base_name}...")
                session_path = run_workflow(
                    video_path=download_info["local_path"],
                    session_name=session_id,
                    sample_fps=SAMPLE_FPS,
                    chunk_frames=CHUNK_FRAMES
                )
                
                if session_path:
                    verification = verify_session(os.path.basename(session_path))
                    log(f"Perception Complete. Verification: {verification}")
                    
                    entry = {
                        "category": category,
                        "title": cand["title"],
                        "url": url,
                        "local_path": download_info["local_path"],
                        "session_path": session_path,
                        "verification": verification,
                        "timestamp": time.time()
                    }
                    manifest["completed_videos"].append(entry)
                    processed_urls.add(url)
                    successful_in_category += 1
                    
                    # Persist manifest after every success
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)
                else:
                    log(f"Workflow failed to generate session for {url}")

                # Be kind to YouTube
                log("Sleeping 2s...")
                time.sleep(2.0)

            except (Exception, BaseException) as e:
                log(f"CRITICAL ERROR processing {url}: {e}")
                log(traceback.format_exc())
                log("Continuing to next candidate...")

    log("Wave Execution Finished.")

if __name__ == "__main__":
    execute_wave()
