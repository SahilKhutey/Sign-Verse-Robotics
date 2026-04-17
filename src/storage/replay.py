import json
import os
import cv2
import time
from typing import Callable, Optional

class ReplayEngine:
    """
    Deterministic Playback Engine for robotic datasets.
    Reconstructs exact sensor capture sequences from archived frames and states.
    """
    def __init__(self, session_path: str):
        self.session_path = session_path
        self.metadata_path = os.path.join(session_path, "metadata.jsonl")
        self.state_path = os.path.join(session_path, "motion_states.jsonl")
        
        # Pre-load pointers for efficiency
        self.metadata = []
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                self.metadata = [json.loads(line) for line in f]

    def play(self, callback: Callable[[cv2.Mat, dict, Optional[dict]], None]):
        """
        Plays back the session in real-time.
        :param callback: Function to handle (frame, metadata, motion_state)
        """
        print(f"[ReplayEngine] Starting playback of {len(self.metadata)} frames...")
        
        # Load motion states if available
        states = {}
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                for line in f:
                    s = json.loads(line)
                    states[round(s['timestamp'], 4)] = s

        for entry in self.metadata:
            frame_idx = entry['frame_index']
            frame_path = os.path.join(self.session_path, "frames", f"frame_{frame_idx:06d}.jpg")
            
            # Load frame
            frame = cv2.imread(frame_path)
            if frame is None:
                continue
                
            # Find closest motion state
            m_state = states.get(round(entry['timestamp'], 4))
            
            # Dispatch
            callback(frame, entry, m_state)
            
            # Temporal alignment (deterministic sleep)
            # Replay assumes target FPS from metadata
            time.sleep(1.0 / 30.0) # Standard 30fps replay logic

    def stream_video(self):
        """Alternative: Replay the merged H.264 video file."""
        video_path = os.path.join(self.session_path, "session_archive.mp4")
        if not os.path.exists(video_path):
            return
            
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Replay Feed", frame)
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
