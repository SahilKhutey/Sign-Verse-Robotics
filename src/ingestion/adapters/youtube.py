import cv2
import yt_dlp
import threading
import time
import os
import re
from typing import Optional, List
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
        self.startup_event = threading.Event()
        self.startup_error: Optional[str] = None

    def _get_stream_url(self):
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][protocol!=m3u8_native]/best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True,
            'cookiesfrombrowser': ('chrome',),  # Bypass bot detection with active session
            'ignoreerrors': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.youtube_url, download=False)
                candidates: List[str] = []
                if info.get('url'):
                    candidates.append(info['url'])
                for fmt in info.get('formats', []):
                    if fmt.get('vcodec') == 'none':
                        continue
                    fmt_url = fmt.get('url')
                    if fmt_url:
                        candidates.append(fmt_url)
                for candidate in candidates:
                    if candidate:
                        return candidate
                return None
        except Exception as e:
            print(f"[YouTubeAdapter] Error extracting URL: {e}")
            return None

    def _open_stream_capture(self, stream_url: str):
        backend_candidates = [None]
        if hasattr(cv2, "CAP_FFMPEG"):
            backend_candidates.insert(0, cv2.CAP_FFMPEG)

        for backend in backend_candidates:
            cap = cv2.VideoCapture(stream_url, backend) if backend is not None else cv2.VideoCapture(stream_url)
            if cap.isOpened():
                return cap
            cap.release()
        return None

    def _ingest_loop(self):
        stream_url = self._get_stream_url()
        if not stream_url:
            self.startup_error = f"Could not resolve YouTube stream: {self.youtube_url}"
            self.startup_event.set()
            self.running = False
            return

        cap = self._open_stream_capture(stream_url)
        if cap is None or not cap.isOpened():
            self.startup_error = f"Could not open YouTube stream: {self.youtube_url}"
            self.startup_event.set()
            self.running = False
            return

        ret, first_frame = cap.read()
        if not ret:
            self.startup_error = f"YouTube stream opened but no frames were readable: {self.youtube_url}"
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
            self.startup_error = None
            self.startup_event.clear()
            self.running = True
            self.thread = threading.Thread(target=self._ingest_loop, daemon=True)
            self.thread.start()
            self.startup_event.wait(timeout=10.0)
            if self.startup_error:
                self.running = False
                raise RuntimeError(self.startup_error)

    @staticmethod
    def search(query: str, max_results: int = 5):
        """
        Static search utility to find YouTube videos for the Dashboard.
        Returns a list of dictionaries with metadata and thumbnails.
        """
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'ignoreerrors': True,
            'no_warnings': True,
        }
        
        # Use ytsearch prefix if it's not a direct URL
        search_query = f"ytsearch{max_results}:{query}"
        
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        # Extract basic metadata with fallbacks
                        vid_id = entry.get('id') or entry.get('url', '').split('v=')[-1]
                        if not vid_id: continue
                        
                        results.append({
                            "title": entry.get("title", "Untitled Motion"),
                            "url": f"https://www.youtube.com/watch?v={vid_id}",
                            "thumbnail": entry.get("thumbnail") or (entry.get("thumbnails", [{}])[0].get("url")),
                            "duration": entry.get("duration", 0),
                            "view_count": entry.get("view_count", 0)
                        })
        except Exception as e:
            print(f"[YouTube Search Error] {e}")
            
        return results

    @staticmethod
    def download_video(youtube_url: str, output_dir: str, filename_prefix: str = "") -> dict:
        """
        Download a YouTube video to local storage for offline pipeline processing.
        Returns metadata including the local file path.
        """
        os.makedirs(output_dir, exist_ok=True)

        ydl_opts = {
            "format": "best[ext=mp4]/best", # Force single-stream to avoid ffmpeg merge dependency
            "quiet": True,
            "noplaylist": True,
            "windowsfilenames": True,
            "restrictfilenames": False,
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "continuedl": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "no_warnings": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            if info is None:
                raise RuntimeError(f"YouTube metadata extraction failed for {youtube_url} (video might be unavailable or private)")
                
            title = info.get("title", "youtube_video")
            video_id = info.get("id", str(int(time.time())))
            safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:80] or "youtube_video"
            prefix = f"{filename_prefix}_" if filename_prefix else ""
            template = os.path.join(output_dir, f"{prefix}{safe_title}_{video_id}.%(ext)s")

            local_opts = dict(ydl_opts)
            local_opts["outtmpl"] = template
            with yt_dlp.YoutubeDL(local_opts) as downloader:
                downloaded_info = downloader.extract_info(youtube_url, download=True)
                local_path = downloader.prepare_filename(downloaded_info)
                if local_path.endswith(".webm") and os.path.exists(local_path[:-5] + ".mp4"):
                    local_path = local_path[:-5] + ".mp4"
                elif local_path.endswith(".mkv") and os.path.exists(local_path[:-4] + ".mp4"):
                    local_path = local_path[:-4] + ".mp4"

        return {
            "title": title,
            "url": youtube_url,
            "video_id": video_id,
            "duration": info.get("duration", 0),
            "local_path": local_path,
        }
