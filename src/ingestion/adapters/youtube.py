import cv2
import yt_dlp
import threading
import time
from typing import Optional
from src.ingestion.schemas import SourceType
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.builder import PacketBuilder
from src.ingestion.bus import StreamBus

class YouTubeAdapter:
    """
    Production-grade YouTube ingestion thread using yt-dlp + OpenCV.
    """
    def __init__(self, 
                 bus: StreamBus, 
                 normalizer: FrameNormalizer, 
                 builder: PacketBuilder,
                 youtube_url: str):
        self.bus = bus
        self.normalizer = normalizer
        self.builder = builder
        self.youtube_url = youtube_url
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _get_stream_url(self):
        ydl_opts = {'format': 'best', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.youtube_url, download=False)
                return info.get('url')
        except Exception as e:
            print(f"[YouTubeAdapter] Error extracting URL: {e}")
            return None

    def _ingest_loop(self):
        stream_url = self._get_stream_url()
        if not stream_url:
            self.running = False
            return

        cap = cv2.VideoCapture(stream_url)
        frame_idx = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # 1. Normalize
            normalized_frame = self.normalizer.process(frame)
            if normalized_frame is None:
                continue

            # 2. Build Packet
            packet = self.builder.build(
                frame_normalized=normalized_frame,
                frame_full_res=frame,
                source_type=SourceType.YOUTUBE,
                source_id=self.youtube_url.split("v=")[-1],
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
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
