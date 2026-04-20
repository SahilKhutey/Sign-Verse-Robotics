import requests
import time
import sys
import os

BASE_URL = "http://localhost:8000"
VIDEO_PATH = r"C:\Users\User\Downloads\test1.mp4"
SESSION_NAME = "test"

def check_backend():
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

def start_workflow():
    print(f"[Mission Control] Starting Workflow for: {VIDEO_PATH}")
    
    # 1. Start Ingestion
    ingest_payload = {
        "source_uri": VIDEO_PATH,
        "source_type": "video_upload"
    }
    r = requests.post(f"{BASE_URL}/ingest/start", json=ingest_payload)
    if r.status_code != 200:
        print(f"[Error] Failed to start ingestion: {r.text}")
        return
    print("[Mission Control] YouTube Ingestion started.")

    # 2. Start Recording
    r = requests.post(f"{BASE_URL}/dataset/start?name={SESSION_NAME}")
    if r.status_code != 200:
        print(f"[Error] Failed to start recording: {r.text}")
        return
    print(f"[Mission Control] Session recording '{SESSION_NAME}' active.")

    # 3. Monitor
    print("[Mission Control] Monitoring process (will wait for video to complete)...")
    while True:
        try:
            r = requests.get(f"{BASE_URL}/api/v1/status")
            if r.status_code == 200:
                status = r.json()
                active_adapters = status.get("active_adapters", [])
                fps = status.get("metrics", {}).get("global", {}).get("fps", 0)
                is_recording = status.get("is_recording", False)
                
                print(f"\r[Status] Active Adapters: {len(active_adapters)} | Global FPS: {fps:.1f} | Recording: {is_recording}", end="")
                
                if not active_adapters:
                    # Video finished
                    print("\n[Mission Control] Video ingestion completed.")
                    break
            else:
                print(f"\n[Error] Status check failed: {r.status_code}")
                break
        except Exception as e:
            print(f"\n[Error] Monitoring exception: {e}")
            break
        time.sleep(2)

    # 4. Stop Recording
    print("[Mission Control] Stopping recording session...")
    r = requests.post(f"{BASE_URL}/dataset/stop")
    if r.status_code == 200:
        print("[Mission Control] Recording stopped.")
    else:
        print(f"[Error] Failed to stop recording: {r.text}")

    # 5. Export 3D Data
    print("[Mission Control] Triggering 3D Generation & Export...")
    r = requests.post(f"{BASE_URL}/dataset/export?name={SESSION_NAME}")
    if r.status_code == 200:
        print("[Mission Control] Export successful! Data ready in /datasets/test/")
    else:
        print(f"[Error] Export failed: {r.text}")

if __name__ == "__main__":
    if not check_backend():
        print("[Error] Backend not reachble at http://localhost:8000. Please start it first.")
        sys.exit(1)
    
    start_workflow()
