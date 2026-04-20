import cv2
import time
import threading
import os
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
        self.startup_event = threading.Event()
        self.startup_error: Optional[str] = None

    def _ingest_loop(self):
        cap = None
        backends = [cv2.CAP_ANY]
        if os.name == 'nt':
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

        for backend in backends:
            candidate = cv2.VideoCapture(self.camera_id, backend)
            if candidate.isOpened():
                cap = candidate
                break
            candidate.release()

        if cap is None:
            self.startup_error = f"Could not open camera {self.camera_id} with any backend"
            print(f"[CameraAdapter Error] {self.startup_error}")
            self.startup_event.set()
            self.running = False
            return

        first_frame = None
        for _ in range(20):
            ret, probe_frame = cap.read()
            if ret:
                first_frame = probe_frame
                break
            time.sleep(0.05)

        if first_frame is None:
            self.startup_error = f"Camera {self.camera_id} opened but did not return frames"
            print(f"[CameraAdapter Error] {self.startup_error}")
            self.startup_event.set()
            self.running = False
            cap.release()
            return

        self.startup_event.set()
        frame_idx = 0
        consecutive_failures = 0
        
        while self.running:
            if first_frame is not None:
                frame = first_frame
                ret = True
                first_frame = None
            else:
                ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures % 30 == 0:
                    print(f"[CameraAdapter Warning] Frame grab failure: {consecutive_failures} consecutive drops.")
                time.sleep(0.01)
                continue
            
            consecutive_failures = 0

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
            self.startup_error = None
            self.startup_event.clear()
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()
            self.startup_event.wait(timeout=4.0)
            if self.startup_error:
                self.running = False
                raise RuntimeError(self.startup_error)
            print(f"[CameraAdapter] Started ingestion on cam {self.camera_id}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            print(f"[CameraAdapter] Stopped ingestion on cam {self.camera_id}")
