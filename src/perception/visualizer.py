import cv2
import numpy as np
from typing import List, Optional
from src.db.schemas import HumanSubject

class SkeletonVisualizer:
    """
    High-fidelity drawing engine for Sign-Verse perception.
    Renders 3D skeletons, hands, and bounding boxes with a neon-aesthetic.
    """
    def __init__(self):
        # Body connection map (MediaPipe standard)
        self.POSE_CONNECTIONS = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
            (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28)
        ]
        # Hand connection map
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20)
        ]

    def draw(self, frame: np.ndarray, subjects: List[HumanSubject]) -> np.ndarray:
        """
        Draws all subject data onto the provided frame.
        """
        canvas = frame.copy()
        h, w = canvas.shape[:2]

        for s in subjects:
            track_missing = int(s.tracking.get("missing_count", 0))
            drift_warning = bool(s.tracking.get("drift_warning", False))
            box_color = (0, 140, 255) if track_missing > 0 else ((0, 64, 255) if drift_warning else (255, 0, 127))

            # 1. Draw Bounding Box (Neon Pink)
            x1, y1, x2, y2 = map(int, s.bbox)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, 1)
            label = f"ID {s.subject_id} | {s.confidence:.2f}"
            if track_missing > 0:
                label += f" | hold {track_missing}"
            elif drift_warning:
                label += " | drift"
            cv2.putText(
                canvas,
                label,
                (x1, max(18, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                box_color,
                1,
                cv2.LINE_AA
            )
            
            # 2. Draw Body Skeleton (Cyan)
            if s.pose and s.pose.skeleton:
                lms = s.pose.skeleton
                for conn in self.POSE_CONNECTIONS:
                    p1 = lms[conn[0]]
                    p2 = lms[conn[1]]
                    if p1.visibility > 0.5 and p2.visibility > 0.5:
                        pt1 = (int(p1.x * w), int(p1.y * h))
                        pt2 = (int(p2.x * w), int(p2.y * h))
                        cv2.line(canvas, pt1, pt2, (255, 255, 0), 2)
                
                # Draw joints
                for lm in lms:
                    if lm.visibility > 0.5:
                        center = (int(lm.x * w), int(lm.y * h))
                        cv2.circle(canvas, center, 3, (255, 255, 255), -1)

            # 3. Draw Hands (White/Blue)
            for hand in [s.left_hand, s.right_hand]:
                if hand and hand.skeleton:
                    lms = hand.skeleton
                    for conn in self.HAND_CONNECTIONS:
                        p1 = lms[conn[0]]
                        p2 = lms[conn[1]]
                        pt1 = (int(p1.x * w), int(p1.y * h))
                        pt2 = (int(p2.x * w), int(p2.y * h))
                        cv2.line(canvas, pt1, pt2, (0, 255, 255), 1)
                    
                    for lm in lms:
                        center = (int(lm.x * w), int(lm.y * h))
                        cv2.circle(canvas, center, 2, (255, 255, 255), -1)

            if s.face and s.face.skeleton:
                nose = s.face.skeleton[1]
                center = (int(nose.x * w), int(nose.y * h))
                cv2.circle(canvas, center, 4, (0, 255, 0), -1)

        return canvas
