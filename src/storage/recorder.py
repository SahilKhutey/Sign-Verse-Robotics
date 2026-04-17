import os
import json
import cv2
import time
import threading
import queue
from typing import Optional, Dict, Any
import numpy as np
from src.ingestion.schemas import UnifiedInputPacket

class DatasetRecorder:
    """
    Hybrid Dataset Recorder for Sign-Verse Robotics.
    Saves synchronous JPEG sequences (for training) and H.264 video (for archiving).
    Operates in a background thread to prevent pipeline stalls.
    """
    def __init__(self, base_path: str = "datasets"):
        self.base_path = base_path
        self.session_id: Optional[str] = None
        self.session_path: Optional[str] = None
        
        # Async writing queue
        self.queue = queue.Queue(maxsize=1000)
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        
        # Format handlers
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.meta_file = None

    def start_session(self, session_name: str, fps: float = 30.0, resolution: tuple = (640, 640)):
        """Initializes a new recording session."""
        self.session_id = f"{session_name}_{int(time.time())}"
        self.session_path = os.path.join(self.base_path, self.session_id)
        
        # Create structure
        os.makedirs(os.path.join(self.session_path, "frames"), exist_ok=True)
        
        # Initialize Video Writer (H.264)
        video_file_path = os.path.join(self.session_path, "session_archive.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(video_file_path, fourcc, fps, resolution)
        
        # Initialize Metadata index
        self.meta_file = open(os.path.join(self.session_path, "metadata.jsonl"), "a")
        
        # Start background worker
        self.running = True
        self.worker_thread = threading.Thread(target=self._writer_worker, daemon=True)
        self.worker_thread.start()
        print(f"[DatasetRecorder] Session started: {self.session_id}")

    def _writer_worker(self):
        """Background thread that consumes frames from the queue and writes to disk."""
        while self.running or not self.queue.empty():
            try:
                packet = self.queue.get(timeout=0.5)
                self._write_to_disk(packet)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[DatasetRecorder Error] Worker failure: {e}")

    def _write_to_disk(self, packet: UnifiedInputPacket):
        # 1. Save JPEG Frame (Deterministic sequence)
        frame_filename = f"frame_{packet.frame_index:06d}.jpg"
        frame_path = os.path.join(self.session_path, "frames", frame_filename)
        cv2.imwrite(frame_path, packet.frame_normalized)
        
        # 2. Add to H.264 Video Stream
        if self.video_writer:
            self.video_writer.write(packet.frame_normalized)
            
        # 3. Write Metadata
        meta_entry = {
            "frame_index": packet.frame_index,
            "timestamp": packet.timestamp,
            "source_id": packet.source_id,
            "sync_id": packet.sync_id,
            "format": "jpeg+h264"
        }
        self.meta_file.write(json.dumps(meta_entry) + "\n")
        self.meta_file.flush()

    def record_packet(self, packet: UnifiedInputPacket):
        """Asynchronously queues a packet for recording."""
        if not self.running:
            return
            
        try:
            self.queue.put_nowait(packet)
        except queue.Full:
            print("[DatasetRecorder Warning] Queue full, dropping record packet.")

    def stop_session(self):
        """Gracefully stops the worker and closes file handles."""
        print(f"[DatasetRecorder] Stopping session {self.session_id}...")
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
            
        if self.video_writer:
            self.video_writer.release()
            
        if self.meta_file:
            self.meta_file.close()
            
        print(f"[DatasetRecorder] Session saved: {self.session_path}")
        self.session_id = None
