import cv2
import time
import threading
import os
from typing import Optional
from src.ingestion.schemas import SourceType
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.builder import PacketBuilder
from src.ingestion.bus import StreamBus

class VideoAdapter:
    """
    Production-grade Video File ingestion thread.
    """
    def __init__(self, 
                 bus: StreamBus, 
                 normalizer: FrameNormalizer, 
                 builder: PacketBuilder,
                 video_path: str):
        self.bus = bus
        self.normalizer = normalizer
        self.builder = builder
        self.video_path = video_path
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.startup_event = threading.Event()
        self.startup_error: Optional[str] = None

    def _ingest_loop(self):
        if not os.path.exists(self.video_path):
            self.startup_error = f"Video not found: {self.video_path}"
            self.startup_event.set()
            self.running = False
            return

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.startup_error = f"Could not open video: {self.video_path}"
            self.startup_event.set()
            self.running = False
            return

        ret, first_frame = cap.read()
        if not ret:
            self.startup_error = f"Video opened but no frames were readable: {self.video_path}"
            self.startup_event.set()
            self.running = False
            cap.release()
            return

        self.startup_event.set()
        frame_idx = 0
        
        while self.running:
            if first_frame is not None:
                frame = first_frame
                ret = True
                first_frame = None
            else:
                ret, frame = cap.read()
            if not ret:
                print(f"[VideoAdapter] Reached end of video: {self.video_path}")
                break

            # 1. Normalize
            normalized_frame = self.normalizer.process(frame)
            if normalized_frame is None:
                continue

            # 2. Build Packet
            packet = self.builder.build(
                frame_normalized=normalized_frame,
                frame_full_res=frame,
                source_type=SourceType.VIDEO,
                source_id=self.video_path.split("/")[-1],
                fps=self.normalizer.target_fps,
                index=frame_idx
            )

            # 3. Push to Bus
            self.bus.push(packet)
            frame_idx += 1

        cap.release()
        self.running = False

    def start(self):
        if not self.running:
            self.startup_error = None
            self.startup_event.clear()
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()
            self.startup_event.wait(timeout=4.0)
            if self.startup_error:
                self.running = False
                raise RuntimeError(self.startup_error)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
