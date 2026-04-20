import sys
import os
import yt_dlp
import cv2
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.perception.orchestrator import PerceptionOrchestrator
from src.ingestion.schemas import SourceType

def smoke_test():
    video_url = 'https://www.youtube.com/watch?v=fRj34o4hN4I'
    output_dir = 'datasets/smoke_test'
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, 'test.mp4')
    
    # 1. Download (Single stream to avoid ffmpeg requirement)
    print(f"--- 1. Downloading Video: {video_url} ---")
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': video_path,
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print(f"Download complete: {video_path}")
    except Exception as e:
        print(f"Download failed: {e}")
        return

    # 2. Initialize Perception
    print("\n--- 2. Initializing Perception Stack ---")
    perception = PerceptionOrchestrator()
    print("Stack ready.")

    # 3. Process first 5 frames
    print("\n--- 3. Processing Frames ---")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video file.")
        return

    for i in range(5):
        ret, frame = cap.read()
        if not ret: break
        
        start = time.time()
        # The method in PerceptionOrchestrator is 'process(frame, timestamp)'
        result = perception.process(frame, timestamp=time.time())
        elapsed = (time.time() - start) * 1000
        
        # result is a FrameData object. Check subjects.
        has_subjects = len(result.subjects) > 0
        
        print(f"Frame {i}: Latency={elapsed:.2f}ms | Subjects={len(result.subjects)}")
        if has_subjects:
            subj = result.subjects[0]
            print(f"   -> Subject {subj.subject_id}: Pose={subj.pose is not None} | Face={subj.face is not None}")

    cap.release()
    print("\nSMOKE TEST COMPLETE.")

if __name__ == "__main__":
    smoke_test()
