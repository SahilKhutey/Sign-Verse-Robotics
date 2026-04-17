import cv2
import time
import threading
from typing import Optional
from src.ingestion.schemas import SourceType
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.builder import PacketBuilder
from src.ingestion.bus import StreamBus

class CameraAdapter:
    """
    Production-grade Live Camera ingestion thread.
    """
    def __init__(self, 
                 bus: StreamBus, 
                 normalizer: FrameNormalizer, 
                 builder: PacketBuilder,
                 camera_id: int = 0):
        self.bus = bus
        self.normalizer = normalizer
        self.builder = builder
        self.camera_id = camera_id
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _ingest_loop(self):
        cap = cv2.VideoCapture(self.camera_id)
        frame_idx = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # 1. Normalize (Temporal & Spatial)
            normalized_frame = self.normalizer.process(frame)
            if normalized_frame is None:
                continue

            # 2. Build Unified Packet (Dual-Res)
            packet = self.builder.build(
                frame_normalized=normalized_frame,
                frame_full_res=frame, # Original quality
                source_type=SourceType.CAMERA,
                source_id=f"cam_{self.camera_id}",
                fps=self.normalizer.target_fps,
                index=frame_idx
            )

            # 3. Push to Bus
            self.bus.push(packet)
            frame_idx += 1

        cap.release()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()
            print(f"[CameraAdapter] Started ingestion on cam {self.camera_id}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            print(f"[CameraAdapter] Stopped ingestion on cam {self.camera_id}")
