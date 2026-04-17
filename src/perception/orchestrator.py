import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional
from src.perception.models.detector import HumanDetector
from src.perception.models.pose import PoseEstimator
from src.perception.models.hands import HandTracker
from src.perception.models.face import FaceAnalyzer
from src.perception.stabilizer import IdentityStabilizer
from src.db.schemas import FrameData, HumanSubject, PoseLandmarks, FaceLandmarks, HandLandmarks

class PerceptionOrchestrator:
    """
    Multi-modal perception command center.
    Orchestrates YOLO, MediaPipe, and adaptive inference for multi-human tracking.
    """
    def __init__(self, use_gpu: bool = True):
        self.detector = HumanDetector()
        self.pose_engine = PoseEstimator()
        self.hand_engine = HandTracker()
        self.face_engine = FaceAnalyzer()
        self.stabilizer = IdentityStabilizer()
        
        # Adaptive Inference Config
        self.detection_interval = 10 # Run YOLO every 10 frames
        self.face_interval = 2      # Run Face Mesh every 2 frames
        self.frame_count = 0
        
        # Tracking state
        self.subjects: Dict[int, Dict[str, Any]] = {} 
        self.next_subject_id = 0

    def process(self, frame: np.ndarray, timestamp: float) -> FrameData:
        """
        Main execution pipeline for a single frame.
        """
        h, w = frame.shape[:2]
        
        # 1. Subject Discovery (YOLOv8)
        detections = []
        if self.frame_count % self.detection_interval == 0 or not self.subjects:
            detections = self.detector.detect(frame)
            self._update_tracking(detections)
            # Stabilize identity after discovery
            self.subjects = self.stabilizer.stabilize(self.subjects)
        
        # 2. Per-Subject Analysis
        human_subjects = []
        for sid, sdata in list(self.subjects.items()):
            bbox = sdata["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            
            # Extract ROI with padding
            pad = 20
            roi_x1, roi_y1 = max(0, x1 - pad), max(0, y1 - pad)
            roi_x2, roi_y2 = min(w, x2 + pad), min(h, y2 + pad)
            crop = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            
            if crop.size == 0:
                continue

            # A. Pose Estimation (Full Fidelity)
            pose = self.pose_engine.process(crop)
            
            # B. Hand Tracking (High Frequency)
            hands = self.hand_engine.process(crop)
            left_hand = next((h for h in hands if h.handedness == 'Left'), None)
            right_hand = next((h for h in hands if h.handedness == 'Right'), None)
            
            # C. Face Mesh (Gated Frequency)
            face = None
            if self.frame_count % self.face_interval == 0:
                face = self.face_engine.process(crop)
                sdata["last_face"] = face
            else:
                face = sdata.get("last_face")

            subject = HumanSubject(
                subject_id=sid,
                bbox=bbox,
                confidence=sdata.get("confidence", 1.0),
                pose=pose,
                face=face,
                left_hand=left_hand,
                right_hand=right_hand
            )
            human_subjects.append(subject)

        # 3. Cleanup & State
        self.frame_count += 1
        
        return FrameData(
            frame_index=self.frame_count,
            timestamp=timestamp,
            subjects=human_subjects
        )

    def _update_tracking(self, detections: List[Dict[str, Any]]):
        """
        Simple centroid-based ID assignment.
        Future optimization: Integration with YOLOv8 native byte-tracker.
        """
        if not detections:
            # Decay tracking confidence or clear if empty for too long
            return

        new_subjects = {}
        for det in detections:
            bbox = det["bbox"]
            centroid = np.array([(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2])
            
            # Find closest existing subject
            best_id = None
            min_dist = 100 # pixels
            
            for sid, sdata in self.subjects.items():
                old_bbox = sdata["bbox"]
                old_centroid = np.array([(old_bbox[0]+old_bbox[2])/2, (old_bbox[1]+old_bbox[3])/2])
                dist = np.linalg.norm(centroid - old_centroid)
                if dist < min_dist:
                    min_dist = dist
                    best_id = sid
            
            if best_id is not None:
                new_subjects[best_id] = {**self.subjects[best_id], "bbox": bbox, "confidence": det["confidence"]}
            else:
                # Add new subject
                new_subjects[self.next_subject_id] = {"bbox": bbox, "confidence": det["confidence"]}
                self.next_subject_id += 1
        
        self.subjects = new_subjects

    def release(self):
        """Clean up MediaPipe resources."""
        self.pose_engine.close()
        self.hand_engine.close()
        self.face_engine.close()
