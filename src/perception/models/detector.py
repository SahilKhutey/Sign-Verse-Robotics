import os
import cv2
import numpy as np
from typing import List, Dict, Any

ULTRALYTICS_CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "scratch", "ultralytics")
)
os.makedirs(ULTRALYTICS_CONFIG_DIR, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", ULTRALYTICS_CONFIG_DIR)

try:
    from ultralytics import YOLO
except ImportError:
    # Fallback/Instructions if not installed
    YOLO = None

class HumanDetector:
    """
    YOLOv8-based multi-human detection engine.
    Provides bounding boxes and crops for targeted landmark extraction.
    """
    def __init__(self, model_variant: str = "models/perception/yolov8n.pt"):
        if YOLO is None:
            print("[HumanDetector] Warning: ultralytics not found. Run 'pip install ultralytics'")
            self.model = None
        else:
            self.model = YOLO(model_variant)

    def detect(self, frame: np.ndarray, confidence: float = 0.3) -> List[Dict[str, Any]]:
        """
        Detects humans and returns bounding boxes with scores.
        """
        if self.model is None:
            return []

        # 1. Direct BGR Inference: Avoid redundant colorspace conversion if possible
        # ultralytics YOLO accepts BGR natively
        bgr_frame = frame

        # Run inference
        results = self.model(bgr_frame, classes=[0], conf=confidence, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                score = float(boxes.conf[i])
                
                detections.append({
                    "bbox": bbox,
                    "confidence": score,
                    "class": "human"
                })
                
        return detections

    def get_crops(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[np.ndarray]:
        """Extracts image regions for sub-model processing."""
        crops = []
        h, w = frame.shape[:2]
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            # Pad crop slightly
            pad = 20
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
            crops.append(frame[y1:y2, x1:x2])
        return crops
