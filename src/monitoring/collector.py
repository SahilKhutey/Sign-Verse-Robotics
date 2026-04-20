import time
import psutil
import numpy as np
from collections import defaultdict, deque
from typing import Dict, Any

class MetricsCollector:
    """
    Production-grade Metrics Aggregator for Sign-Verse Robotics.
    Tracks sub-second FPS, rolling latency, and frame drops per source.
    """
    def __init__(self, window_size: int = 100):
        self.fps_counter = defaultdict(int)
        self.last_time = defaultdict(lambda: time.time())
        
        # source_id -> rolling window of values
        self.latency_buffer = defaultdict(lambda: deque(maxlen=window_size))
        self.drop_buffer = defaultdict(int)
        self.frame_count = defaultdict(int)
        self.current_intent = "IDLE"
        self.intent_confidence = 0.0
        self.subject_count = 0
        self.stability_health = 1.0
        
        # Stitch Dashboard Telemetry Fields
        self.cpu_usage = 0.0
        self.robot_velocity = [0.0, 0.0, 0.0]
        self.total_power_drain = 120.0 # Baseline watts
        self.hand_embedding = np.zeros(64).tolist()
        self.hand_joints = []
        self.bridge_status = {
            "blender": False,
            "isaac": False
        }
        
        # ML Training Telemetry
        self.training_metrics = {
            "epoch": 0,
            "loss": 0.0,
            "accuracy": 0.0,
            "val_loss": 0.0,
            "dataset_size": 0,
            "is_training": False
        }

    def record_stability(self, health: float):
        """Records physical stability health (0.0 to 1.0)."""
        self.stability_health = health

    def update_subject_count(self, count: int):
        """Updates the number of active subjects tracked by perception."""
        self.subject_count = count

    def record_frame(self, source_id: str):
        """Signals that a frame has been ingested."""
        self.fps_counter[source_id] += 1
        self.frame_count[source_id] += 1

    def record_latency(self, source_id: str, latency: float):
        """Records end-to-end latency in seconds."""
        self.latency_buffer[source_id].append(latency)

    def record_drops(self, source_id: str, count: int):
        """Records detected frame drops."""
        self.drop_buffer[source_id] += count

    def record_intent(self, intent: str, confidence: float):
        """Captures decoded human intent for telemetry."""
        self.current_intent = intent
        self.intent_confidence = confidence

    def record_rl_latency(self, latency_ms: float):
        """Specifically tracks RL decision latency for Audit Point 13."""
        self.latency_buffer["rl_decision"].append(latency_ms / 1000.0)

    def record_control_latency(self, latency_ms: float):
        """Specifically tracks WBC/MPC latency for Audit Point 13."""
        self.latency_buffer["control_update"].append(latency_ms / 1000.0)
        
    def record_robot_state(self, velocity: list, power_drain: float):
        """Records state specifically for STITCH Advanced HUD."""
        self.robot_velocity = velocity
        self.total_power_drain = power_drain

    def record_training(self, epoch: int, loss: float, acc: float, val_loss: float = 0.0, is_training: bool = True):
        """Captures ML Pipeline training telemetry."""
        self.training_metrics.update({
            "epoch": epoch,
            "loss": loss,
            "accuracy": acc,
            "val_loss": val_loss,
            "is_training": is_training
        })

    def update_dataset_stats(self, size: int):
        self.training_metrics["dataset_size"] = size

    def compute_fps(self, source_id: str) -> float:
        """Calculates current FPS based on the elapsed time since the last window."""
        now = time.time()
        elapsed = now - self.last_time[source_id]
        
        if elapsed < 0.1: # Threshold to avoid jitter on low samples
            return 0.0

        fps = self.fps_counter[source_id] / elapsed
        
        # Reset counter for next window
        self.fps_counter[source_id] = 0
        self.last_time[source_id] = now
        
        return round(fps, 2)

    def get_avg_latency(self, source_id: str) -> float:
        """Returns average latency in milliseconds."""
        buf = self.latency_buffer[source_id]
        if not buf:
            return 0.0
        return round((sum(buf) / len(buf)) * 1000.0, 2)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Returns a complete snapshot of the system metrics for the dashboard."""
        stats = {}
        # Refresh CPU
        self.cpu_usage = psutil.cpu_percent(interval=None)
        
        # Always output global system metrics
        stats["global"] = {
            "fps": 0.0,
            "latency_ms": 0.0,
            "total_drops": 0,
            "total_frames": 0,
            "current_intent": self.current_intent,
            "intent_confidence": self.intent_confidence,
            "active_subjects": self.subject_count,
            "rl_latency_ms": self.get_avg_latency("rl_decision"),
            "control_latency_ms": self.get_avg_latency("control_update"),
            "stability_health": self.stability_health,
            "cpu_usage": self.cpu_usage,
            "robot_velocity": self.robot_velocity,
            "total_power_drain": self.total_power_drain,
            "skeleton_version": getattr(self, "skeleton_version", "v.3.2 (Full)"),
            "hand_embedding": self.hand_embedding,
            "hand_joints": self.hand_joints,
            "bridge_status": self.bridge_status,
            "training": self.training_metrics
        }

        for source_id in list(self.last_time.keys()):
            if source_id in ["rl_decision", "control_update"]:
                continue
                
            stats[source_id] = {
                "fps": self.compute_fps(source_id),
                "latency_ms": self.get_avg_latency(source_id),
                "total_drops": self.drop_buffer[source_id],
                "total_frames": self.frame_count[source_id],
                "current_intent": self.current_intent,
                "intent_confidence": self.intent_confidence,
                "active_subjects": self.subject_count,
                "rl_latency_ms": self.get_avg_latency("rl_decision"),
                "control_latency_ms": self.get_avg_latency("control_update"),
                "stability_health": self.stability_health,
                "cpu_usage": self.cpu_usage,
                "robot_velocity": self.robot_velocity,
                "total_power_drain": self.total_power_drain,
                "skeleton_version": getattr(self, "skeleton_version", "v.3.2 (Full)"),
                "hand_embedding": self.hand_embedding,
                "hand_joints": self.hand_joints
            }
        return stats
