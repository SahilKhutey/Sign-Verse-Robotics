import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional
from src.perception.models.detector import HumanDetector
from src.perception.models.pose import PoseEstimator
from src.perception.models.hands import HandTracker
from src.perception.models.face import FaceAnalyzer
from src.perception.stabilizer import IdentityStabilizer
from src.perception.downloader import ensure_models
from src.db.schemas import FrameData, HumanSubject, PoseLandmarks, FaceLandmarks, HandLandmarks, Joint

class PerceptionOrchestrator:
    """
    Multi-modal perception command center.
    Orchestrates YOLO, MediaPipe, and adaptive inference for multi-human tracking.
    """
    def __init__(self, use_gpu: bool = True):
        # Ensure Task models are downloaded for Python 3.14 compatibility
        ensure_models()
        
        self.detector = HumanDetector()
        self.pose_engine = PoseEstimator()
        self.hand_engine = HandTracker()
        self.face_engine = FaceAnalyzer()
        self.stabilizer = IdentityStabilizer()
        
        # Adaptive Inference Config
        self.detection_interval = 10 # Run YOLO every 10 frames
        self.face_interval = 2      # Run Face Mesh every 2 frames
        self.frame_count = 0
        self.track_max_age = 12
        self.min_subject_area = 3500
        self.max_tracking_distance = 160.0
        
        # Tracking state
        self.subjects: Dict[int, Dict[str, Any]] = {} 
        self.next_subject_id = 0
        
        # Performance: Parallel Worker Pool
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Hardening: Detail Cap (Determined by Orchestrator based on GPU)
        self.detail_cap = 2 
        self.force_cpu = False # Fallback flag

    def process(self, frame: np.ndarray, timestamp: float) -> FrameData:
        """
        Main execution pipeline for a single frame.
        """
        h, w = frame.shape[:2]

        # 1. Subject Discovery (YOLOv8)
        detections = []
        if self.frame_count % self.detection_interval == 0 or not self.subjects:
            detections = self.detector.detect(frame)
            if detections and self.frame_count % 120 == 0:
                print(f"[Perception] Discovery: Identified {len(detections)} potential subject(s)")
            self._update_tracking(detections)
            self.subjects = self.stabilizer.stabilize(self.subjects)
        else:
            for sid in list(self.subjects.keys()):
                self.subjects[sid]["missing_count"] = self.subjects[sid].get("missing_count", 0) + 1
                if self.subjects[sid]["missing_count"] > self.track_max_age:
                    self._drop_subject(sid)
        
        if not self.subjects and self.frame_count % 30 == 0:
            print("[Perception] discovery heartbeat: No subjects found in environment.")
        
        # 2. Per-Subject Analysis (Parallelized & Adaptive Detail Gating)
        human_subjects = []
        
        sorted_sids = sorted(
            self.subjects.keys(), 
            key=lambda sid: (self.subjects[sid]["bbox"][2]-self.subjects[sid]["bbox"][0]) * 
                            (self.subjects[sid]["bbox"][3]-self.subjects[sid]["bbox"][1]),
            reverse=True
        )

        # Batch process primary and secondary subjects
        tasks = []
        for i, sid in enumerate(sorted_sids):
            # Pass detail gating level based on rank and cap
            detail_level = 2 if i < self.detail_cap else 0 # 2=Full, 1=Pose+Hands, 0=PoseOnly
            tasks.append((sid, detail_level, frame, w, h))

        # Run multi-modal inference in parallel threads to maximize GPU/CPU overlap
        results = list(self.executor.map(lambda p: self._analyze_subject(*p), tasks))
        human_subjects = [s for s in results if s is not None]

        self.frame_count += 1

        return FrameData(
            frame_index=self.frame_count,
            timestamp=timestamp,
            subjects=human_subjects,
        )

    def _analyze_subject(self, sid: int, detail_level: int, frame: np.ndarray, w: int, h: int) -> Optional[HumanSubject]:
        """Parallel-safe subject analysis."""
        sdata = self.subjects.get(sid)
        if not sdata: return None
        
        bbox = sdata["bbox"]
        x1, y1, x2, y2 = map(int, bbox)
        area = (x2-x1) * (y2-y1)
        
        if area < self.min_subject_area:
            return None

        # Extract ROI
        pad = 15
        rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
        rx2, ry2 = min(w, x2 + pad), min(h, y2 + pad)
        crop = frame[ry1:ry2, rx1:rx2]
        if crop.size == 0: return None

        # 1. Pose (Required for all subjects)
        pose = self._to_global_pose(self.pose_engine.process(crop), rx1, ry1, rx2 - rx1, ry2 - ry1, w, h)
        
        # 2. Detail Analysis (Hands/Face) based on gating
        hands = []
        face = None
        
        if detail_level >= 1: # Full detail
             # Note: HandTracker and FaceAnalyzer must be thread-safe or locked
             hands = self._to_global_hands(self.hand_engine.process(crop), rx1, ry1, rx2 - rx1, ry2 - ry1, w, h)
             if detail_level >= 2 and self.frame_count % self.face_interval == 0:
                 face = self._to_global_face(self.face_engine.process(crop), rx1, ry1, rx2 - rx1, ry2 - ry1, w, h)
                 sdata["last_face"] = face
             else:
                 face = sdata.get("last_face")

        # Persistence
        if pose: sdata["last_pose"] = pose
        else: pose = sdata.get("last_pose")
        
        if hands: sdata["last_hands"] = hands
        else: hands = sdata.get("last_hands", [])

        left_hand = next((h for h in hands if h.handedness == 'Left'), None)
        right_hand = next((h for h in hands if h.handedness == 'Right'), None)

        return HumanSubject(
            subject_id=sid,
            bbox=bbox,
            confidence=sdata.get("confidence", 1.0),
            pose=pose,
            face=face,
            left_hand=left_hand,
            right_hand=right_hand,
            tracking={
                "missing_count": sdata.get("missing_count", 0),
                "last_seen_frame": sdata.get("last_seen_frame", self.frame_count),
                "drift_warning": sdata.get("drift_warning", False),
                "centroid_distance": self.stabilizer.centroid_distance(sid, bbox),
            }
        )

    def _update_tracking(self, detections: List[Dict[str, Any]]):
        """
        Simple centroid-based ID assignment.
        Future optimization: Integration with YOLOv8 native byte-tracker.
        """
        if not detections:
            for sid in list(self.subjects.keys()):
                self.subjects[sid]["missing_count"] = self.subjects[sid].get("missing_count", 0) + 1
                if self.subjects[sid]["missing_count"] > self.track_max_age:
                    self._drop_subject(sid)
            return

        existing_ids = set(self.subjects.keys())
        updated_subjects: Dict[int, Dict[str, Any]] = {}
        assigned_ids = set()
        unmatched_detections = []

        for det in detections:
            bbox = det["bbox"]
            best_id = None
            best_score = -1.0
            for sid in existing_ids - assigned_ids:
                score = self._association_score(bbox, self.subjects[sid]["bbox"])
                if score > best_score:
                    best_score = score
                    best_id = sid

            if best_id is not None and best_score > 0.0:
                updated_subjects[best_id] = {
                    **self.subjects[best_id],
                    "bbox": bbox,
                    "confidence": det["confidence"],
                    "missing_count": 0,
                    "last_seen_frame": self.frame_count,
                }
                assigned_ids.add(best_id)
            else:
                unmatched_detections.append(det)

        for sid in existing_ids - assigned_ids:
            stale = {**self.subjects[sid]}
            stale["missing_count"] = stale.get("missing_count", 0) + 1
            if stale["missing_count"] <= self.track_max_age:
                updated_subjects[sid] = stale
            else:
                self.stabilizer.purge_id(sid)

        for det in unmatched_detections:
            updated_subjects[self.next_subject_id] = {
                "bbox": det["bbox"],
                "confidence": det["confidence"],
                "missing_count": 0,
                "last_seen_frame": self.frame_count,
            }
            self.next_subject_id += 1
        
        self.subjects = updated_subjects

    def _association_score(self, bbox_a: List[float], bbox_b: List[float]) -> float:
        centroid_a = np.array([(bbox_a[0] + bbox_a[2]) / 2, (bbox_a[1] + bbox_a[3]) / 2], dtype=np.float32)
        centroid_b = np.array([(bbox_b[0] + bbox_b[2]) / 2, (bbox_b[1] + bbox_b[3]) / 2], dtype=np.float32)
        centroid_dist = np.linalg.norm(centroid_a - centroid_b)
        if centroid_dist > self.max_tracking_distance:
            return -1.0
        iou = self._bbox_iou(bbox_a, bbox_b)
        distance_term = 1.0 - (centroid_dist / self.max_tracking_distance)
        return (0.65 * iou) + (0.35 * distance_term)

    def _bbox_iou(self, bbox_a: List[float], bbox_b: List[float]) -> float:
        ax1, ay1, ax2, ay2 = bbox_a
        bx1, by1, bx2, by2 = bbox_b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter_area
        return float(inter_area / union) if union > 0 else 0.0

    def _drop_subject(self, sid: int):
        if sid in self.subjects:
            del self.subjects[sid]
        self.stabilizer.purge_id(sid)

    def _project_joint(self, joint: Joint, roi_x: int, roi_y: int, roi_w: int, roi_h: int, frame_w: int, frame_h: int) -> Joint:
        scale = max(roi_w, roi_h) / max(frame_w, frame_h, 1)
        global_x = (roi_x + (joint.x * roi_w)) / max(frame_w, 1)
        global_y = (roi_y + (joint.y * roi_h)) / max(frame_h, 1)
        return Joint(
            x=float(np.clip(global_x, 0.0, 1.0)),
            y=float(np.clip(global_y, 0.0, 1.0)),
            z=float(joint.z * scale),
            visibility=joint.visibility,
            presence=joint.presence,
        )

    def _to_global_pose(self, pose: Optional[PoseLandmarks], roi_x: int, roi_y: int, roi_w: int, roi_h: int, frame_w: int, frame_h: int) -> Optional[PoseLandmarks]:
        if pose is None:
            return None
        return PoseLandmarks(
            skeleton=[self._project_joint(j, roi_x, roi_y, roi_w, roi_h, frame_w, frame_h) for j in pose.skeleton]
        )

    def _to_global_hands(self, hands: List[HandLandmarks], roi_x: int, roi_y: int, roi_w: int, roi_h: int, frame_w: int, frame_h: int) -> List[HandLandmarks]:
        return [
            HandLandmarks(
                skeleton=[self._project_joint(j, roi_x, roi_y, roi_w, roi_h, frame_w, frame_h) for j in hand.skeleton],
                handedness=hand.handedness,
                score=hand.score,
            )
            for hand in hands
        ]

    def _to_global_face(self, face: Optional[FaceLandmarks], roi_x: int, roi_y: int, roi_w: int, roi_h: int, frame_w: int, frame_h: int) -> Optional[FaceLandmarks]:
        if face is None:
            return None
        return FaceLandmarks(
            skeleton=[self._project_joint(j, roi_x, roi_y, roi_w, roi_h, frame_w, frame_h) for j in face.skeleton]
        )

    def release(self):
        """Clean up MediaPipe resources."""
        self.pose_engine.close()
        self.hand_engine.close()
        self.face_engine.close()
