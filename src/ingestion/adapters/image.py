import cv2
import time
import threading
import os
from typing import Optional, Union, Any
import numpy as np
from src.ingestion.schemas import SourceType
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.builder import PacketBuilder
from src.ingestion.bus import StreamBus

class ImageAdapter:
    """
    Adapter for processing static images as a continuous loop.
    Supports both local filesystem paths and raw image arrays (from uploads).
    """
    def __init__(self, 
                 bus: StreamBus, 
                 normalizer: FrameNormalizer, 
                 builder: PacketBuilder,
                 image_source: Union[str, np.ndarray]):
        self.bus = bus
        self.normalizer = normalizer
        self.builder = builder
        self.image_source = image_source
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.startup_event = threading.Event()
        self.startup_error: Optional[str] = None

    def _ingest_loop(self):
        # 1. Load image
        if isinstance(self.image_source, str):
            if not os.path.exists(self.image_source):
                self.startup_error = f"Image not found: {self.image_source}"
                self.startup_event.set()
                self.running = False
                return
            frame = cv2.imread(self.image_source)
        else:
            frame = self.image_source

        if frame is None:
            self.startup_error = f"Could not load image from {self.image_source}"
            print(f"[ImageAdapter Error] {self.startup_error}")
            self.startup_event.set()
            self.running = False
            return

        self.startup_event.set()

        frame_idx = 0
        
        while self.running:
            # 2. Normalize
            normalized_frame = self.normalizer.process(frame)
            if normalized_frame is None:
                continue

            # 3. Build Packet
            packet = self.builder.build(
                frame_normalized=normalized_frame,
                frame_full_res=frame,
                source_type=SourceType.IMAGE,
                source_id="static_input",
                fps=self.normalizer.target_fps,
                index=frame_idx
            )

            # 4. Push to Bus
            self.bus.push(packet)
            frame_idx += 1
            
            # Maintain target FPS (default 30)
            time.sleep(1.0 / self.normalizer.target_fps)

    def start(self):
        if not self.running:
            self.startup_error = None
            self.startup_event.clear()
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()
            self.startup_event.wait(timeout=3.0)
            if self.startup_error:
                self.running = False
                raise RuntimeError(self.startup_error)
            print("[ImageAdapter] Started static loop ingestion.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            print("[ImageAdapter] Stopped static loop ingestion.")
