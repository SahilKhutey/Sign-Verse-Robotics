import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.run_video_batch import run_batch
from scripts.generate_batch_report import generate_report

INTERRUPTED_JOB_ID = "autoyt_20260420_161547_09b662"
JOB_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "datasets", "auto_jobs", INTERRUPTED_JOB_ID, "job_manifest.json")

def resume_job():
    print(f"!!! SIGN-VERSE JOB RECOVERY: {INTERRUPTED_JOB_ID} !!!")
    
    if not os.path.exists(JOB_MANIFEST_PATH):
        print(f"[ERROR] Manifest not found at {JOB_MANIFEST_PATH}")
        return

    with open(JOB_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    download_dir = os.path.join(PROJECT_ROOT, manifest["download_dir"])
    if not os.path.isdir(download_dir):
        print(f"[ERROR] Download directory not found at {download_dir}")
        return

    print(f"[1/3] RESUMING WORKFLOW ON: {download_dir}")
    print(f"[INFO] Videos to process: {len(manifest['downloaded_videos'])}")
    
    try:
        # Step 1: Run the perception/mapping batch
        batch_dir = run_batch(download_dir, chunk_frames=manifest.get("chunk_frames", 100), sample_fps_override=manifest.get("sample_fps", 30.0))
        
        # Step 2: Generate reports
        print(f"[2/3] GENERATING CONSOLIDATED REPORTS FOR: {batch_dir}")
        report_paths = generate_report(batch_dir)
        
        # Step 3: Update manifest
        print(f"[3/3] FINALIZING JOB MANIFEST")
        manifest["status"] = "completed"
        manifest["phase"] = "completed"
        manifest["message"] = "Recovery successful. Job completed."
        manifest["batch_dir"] = os.path.relpath(batch_dir, PROJECT_ROOT)
        manifest["batch_id"] = os.path.basename(batch_dir)
        manifest["report_paths"] = report_paths
        manifest["finished_at"] = time.time()
        
        with open(JOB_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        print("\n" + "="*60)
        print(" SUCCESS: JOB COMPLETED AND MANIFEST UPDATED")
        print(f" BATCH ID: {manifest['batch_id']}")
        print("="*60)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Job recovery failed: {e}")
        manifest["status"] = "error"
        manifest["error"] = str(e)
        with open(JOB_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    resume_job()
