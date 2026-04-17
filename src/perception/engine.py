import cv2
import mediapipe as mp
import numpy as np
from typing import List, Optional, Tuple, Dict
from src.db.schemas import FrameData, Joint, PoseLandmarks, FaceLandmarks, HandLandmarks
from src.ingestion.structured_frame import StructuredFrame

class PerceptionEngine:
    def __init__(self, 
                 static_image_mode=False, 
                 model_complexity=1, 
                 smooth_landmarks=True, 
                 min_detection_confidence=0.5, 
                 min_tracking_confidence=0.5):
        
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def _convert_landmarks(self, landmarks) -> List[Joint]:
        if not landmarks:
            return []
        return [
            Joint(
                x=lm.x, 
                y=lm.y, 
                z=lm.z, 
                visibility=getattr(lm, 'visibility', 1.0),
                presence=getattr(lm, 'presence', 1.0)
            ) for lm in landmarks.landmark
        ]

    def process_frame(self, frame_obj: StructuredFrame) -> FrameData:
        """
        Processes a StructuredFrame (RGB float32) and returns structured FrameData.
        Ensures compatibility with MediaPipe's expectations.
        """
        # MediaPipe Holistic works best with uint8 RGB.
        # Our pipeline provides float32 [0, 1] RGB.
        if frame_obj.frame.dtype == np.float32:
            image_to_process = (frame_obj.frame * 255).astype(np.uint8)
        else:
            image_to_process = frame_obj.frame

        results = self.holistic.process(image_to_process)

        frame_data = FrameData(
            frame_index=frame_obj.sequence_index,
            timestamp=frame_obj.timestamp,
            pose=None,
            face=None,
            left_hand=None,
            right_hand=None
        )

        # Extract Pose
        if results.pose_landmarks:
            frame_data.pose = PoseLandmarks(skeleton=self._convert_landmarks(results.pose_landmarks))

        # Extract Face
        if results.face_landmarks:
            frame_data.face = FaceLandmarks(skeleton=self._convert_landmarks(results.face_landmarks))

        # Extract Hands
        if results.left_hand_landmarks:
            frame_data.left_hand = HandLandmarks(
                skeleton=self._convert_landmarks(results.left_hand_landmarks),
                handedness="Left",
                score=1.0 # Default for mp holistic
            )
        
        if results.right_hand_landmarks:
            frame_data.right_hand = HandLandmarks(
                skeleton=self._convert_landmarks(results.right_hand_landmarks),
                handedness="Right",
                score=1.0
            )

        return frame_data

    def draw_landmarks(self, frame: np.ndarray, frame_data: FrameData):
        """
        Utility to draw detected landmarks back onto the frame for debugging/visualization.
        NOTE: This is a simplified version using mp drawing utils directly on the original results 
        if we kept them, but here we'll simulate or use the schemas.
        """
        # For professional visualization, we'd typically use the schemas. 
        # For now, this is a placeholder for the UI overlay logic.
        pass

    def release(self):
        self.holistic.close()

if __name__ == "__main__":
    # Test script for local verification
    cap = cv2.VideoCapture(0)
    engine = PerceptionEngine()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        data = engine.process_frame(frame, 0, 0.0)
        if data.pose:
            print(f"Pose detected: {len(data.pose.skeleton)} joints")
            
        cv2.imshow('Sign-Verse Perception Test', frame)
        if cv2.waitKey(5) & 0xFF == 27:
            break
            
    engine.release()
    cap.release()
    cv2.destroyAllWindows()
