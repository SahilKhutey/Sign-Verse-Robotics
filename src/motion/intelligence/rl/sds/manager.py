import torch
import os
import time
from typing import Dict, Any, List

class PolicyVersionManager:
    """
    Handles RL Policy Versioning, Weight Snapshots, and Auto-Rollback logic.
    Rolls back to 'Last Known Good' if social engagement thresholds fail in production.
    """
    def __init__(self, 
                 model: Any, 
                 version_dir: str = "models/rl_policy/versions",
                 rollback_threshold: float = 0.3,
                 rollback_window: int = 300): # 5 Minutes
        self.model = model
        self.version_dir = version_dir
        self.rollback_threshold = rollback_threshold
        self.rollback_window = rollback_window
        
        # Monitoring state
        self.engagement_buffer: List[float] = []
        self.last_rollback_check = time.time()
        self.last_good_version = "v1.0"

    def snapshot(self, version_name: str):
        """Saves a named snapshot of the current policy weights."""
        path = os.path.join(self.version_dir, f"{version_name}.pt")
        torch.save(self.model.state_dict(), path)
        self.last_good_version = version_name
        print(f"📦 Policy Snapshot Created: {version_name}")

    def load_version(self, version_name: str):
        """Loads a specific weight version."""
        path = os.path.join(self.version_dir, f"{version_name}.pt")
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location='cpu'))
            print(f"📦 Policy Reverted to: {version_name}")
        else:
            print(f"❌ Version {version_name} not found.")

    def track_engagement(self, engagement: float):
        """
        Record engagement for auto-rollback monitoring.
        Triggered by the Inference Engine.
        """
        self.engagement_buffer.append(engagement)
        
        # Check window
        current_time = time.time()
        if (current_time - self.last_rollback_check) >= self.rollback_window:
            self._check_health()
            self.last_rollback_check = current_time
            self.engagement_buffer = []

    def _check_health(self):
        """Evaluates model performance vs threshold."""
        if not self.engagement_buffer:
            return
            
        avg_eng = sum(self.engagement_buffer) / len(self.engagement_buffer)
        if avg_eng < self.rollback_threshold:
            print(f"🚨 Social Health Crisis: Avg Engagement {avg_eng:.2f} < {self.rollback_threshold}")
            print("🚨 Triggering Auto-Rollback to last stable version...")
            self.load_version(self.last_good_version)
