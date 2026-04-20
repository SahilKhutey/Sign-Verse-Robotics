import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
import os
from typing import Optional, List
from src.db.schemas import PoseLandmarks, Joint

class PoseEstimator:
    """
    Modern MediaPipe Tasks-based Pose Estimation wrapper.
    Migrated for compatibility with Python 3.14.
    Balanced for performance using 'full' instead of 'heavy' by default.
    """
    def __init__(self, complexity: str = "full"):
        """
        complexity: 'lite', 'full', or 'heavy'
        """
        model_filename = f"pose_landmarker_{complexity}.task"
        model_path = os.path.join("models/perception", model_filename)

        if not os.path.exists(model_path):
            print(f"[PoseEstimator] Warning: Model not found at {model_path}. Fallback to full.")
            model_path = "models/perception/pose_landmarker_full.task"

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            output_segmentation_masks=False
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray) -> Optional[PoseLandmarks]:
        """
        Processes a single RGB image (or crop) and returns PoseLandmarks.
        """
        if self.landmarker is None:
            return None

        # MediaPipe Task API expects mp.Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        try:
            results = self.landmarker.detect(mp_image)
        except Exception as e:
            print(f"[PoseEstimator] Detection error: {e}")
            return None

        if not results.pose_landmarks:
            return None

        # Take the primary subject in the crop
        first_person = results.pose_landmarks[0]
        
        landmarks = [
            Joint(
                x=lm.x, y=lm.y, z=lm.z, 
                visibility=lm.visibility, 
                presence=getattr(lm, 'presence', 0.0)
            ) for lm in first_person
        ]

        return PoseLandmarks(skeleton=landmarks)

    def close(self):
        if self.landmarker:
            self.landmarker.close()
