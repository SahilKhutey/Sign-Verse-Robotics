import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
import os
from typing import Optional
from src.db.schemas import FaceLandmarks, Joint

class FaceAnalyzer:
    """
    Modern MediaPipe Tasks-based Face Mesh wrapper.
    Migrated for compatibility with Python 3.14.
    """
    def __init__(self, model_path: str = "models/perception/face_landmarker.task", static_mode: bool = False):
        if not os.path.exists(model_path):
            print(f"[FaceAnalyzer] Warning: Model not found at {model_path}")
            self.landmarker = None
            return

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray) -> Optional[FaceLandmarks]:
        """
        Processes a single RGB image (or crop) and returns FaceLandmarks.
        """
        if self.landmarker is None:
            return None

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        try:
            results = self.landmarker.detect(mp_image)
        except Exception as e:
            print(f"[FaceAnalyzer] Detection error: {e}")
            return None

        if not results.face_landmarks:
            return None

        # Take primary face from crop
        face_lms = results.face_landmarks[0]
        landmarks = [
            Joint(
                x=lm.x, y=lm.y, z=lm.z, 
                visibility=1.0, 
                presence=1.0
            ) for lm in face_lms
        ]

        return FaceLandmarks(skeleton=landmarks)

    def close(self):
        if self.landmarker:
            self.landmarker.close()
