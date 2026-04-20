import os
import urllib.request
from typing import Dict

MODELS: Dict[str, str] = {
    "pose_landmarker_lite.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
    "pose_landmarker_full.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
    "pose_landmarker_heavy.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task",
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
}

def ensure_models(target_dir: str = "models/perception"):
    """
    Ensures that required MediaPipe Task models are present.
    Downloads them from Google CDN if missing.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        print(f"[Downloader] Created directory: {target_dir}")

    for filename, url in MODELS.items():
        filepath = os.path.join(target_dir, filename)
        if not os.path.exists(filepath):
            print(f"[Downloader] Downloading {filename} from MediaPipe CDN...")
            try:
                urllib.request.urlretrieve(url, filepath)
                print(f"[Downloader] Successfully downloaded {filename}")
            except Exception as e:
                print(f"[Downloader] Error downloading {filename}: {e}")
        else:
            # print(f"[Downloader] {filename} already exists.")
            pass

if __name__ == "__main__":
    ensure_models()
