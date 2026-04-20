import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
import os
from typing import List, Optional
from src.db.schemas import HandLandmarks, Joint

class HandTracker:
    """
    Modern MediaPipe Tasks-based Hand Tracking wrapper.
    Migrated for compatibility with Python 3.14.
    """
    def __init__(self, model_path: str = "models/perception/hand_landmarker.task", max_hands: int = 2):
        if not os.path.exists(model_path):
            print(f"[HandTracker] Warning: Model not found at {model_path}")
            self.landmarker = None
            return

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray) -> List[HandLandmarks]:
        """
        Processes a single RGB image (or crop) and returns a list of HandLandmarks.
        """
        if self.landmarker is None:
            return []

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        try:
            results = self.landmarker.detect(mp_image)
        except Exception as e:
            print(f"[HandTracker] Detection error: {e}")
            return []

        hand_results = []
        if not results.hand_landmarks:
            return []

        for i, hand_lms in enumerate(results.hand_landmarks):
            # Tasks API returns handedness as categories
            handedness = results.handedness[i][0].category_name if results.handedness else "Unknown"
            score = results.handedness[i][0].score if results.handedness else 0.0

            landmarks = [
                Joint(
                    x=lm.x, y=lm.y, z=lm.z, 
                    visibility=1.0, 
                    presence=1.0
                ) for lm in hand_lms
            ]

            hand_results.append(HandLandmarks(
                skeleton=landmarks,
                handedness=handedness,
                score=score
            ))

        return hand_results

    def close(self):
        if self.landmarker:
            self.landmarker.close()
