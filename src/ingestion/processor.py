import cv2
import yt_dlp
import os
import time
from typing import Generator, Optional, Tuple
import numpy as np

class IngestionProcessor:
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def get_youtube_stream_url(self, youtube_url: str) -> Optional[str]:
        """
        Extracts the best stream URL from a YouTube link using yt-dlp.
        """
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info.get('url')
        except Exception as e:
            print(f"Error fetching YouTube stream: {e}")
            return None

    def stream_frames(self, source: str, is_youtube: bool = False) -> Generator[Tuple[np.ndarray, int, float, float], None, None]:
        """
        Generator that yields (frame, frame_index, timestamp, fps).
        """
        if is_youtube:
            stream_url = self.get_youtube_stream_url(source)
            if not stream_url:
                return
            source = stream_url

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Error: Could not open video source {source}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_index = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            timestamp = frame_index / fps
            yield frame, frame_index, timestamp, fps
            frame_index += 1

        cap.release()

if __name__ == "__main__":
    # Small test
    processor = IngestionProcessor()
    # Testing with a local video or youtube placeholder
    # for frame, idx, ts, fps in processor.stream_frames("path/to/video.mp4"):
    #     cv2.imshow("Frame", frame)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    pass
