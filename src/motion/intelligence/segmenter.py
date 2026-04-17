import numpy as np
from src.motion.core.state import MotionState

class ActionSegmenter:
    """
    Intelligence module to split continuous motion into discrete action chunks.
    Uses velocity-derivative thresholds to detect start/stop triggers.
    """
    def __init__(self, threshold: float = 0.02):
        self.threshold = threshold
        self.is_moving = False
        self._prev_velocity_mag = 0.0

    def update_threshold(self, value: float):
        """Allows real-time tuning from the dashboard."""
        self.threshold = value

    def detect_trigger(self, state: MotionState) -> bool:
        """
        Analyzes kinematic state to detect a significant change in motion.
        Returns True if a motion 'start' or 'stop' is detected.
        """
        if state.joint_velocities is None:
            return False

        # Calculate mean magnitude of joint velocities
        # This provides a 'Global Activity' level for the skeleton
        current_velocity_mag = np.mean(np.linalg.norm(state.joint_velocities, axis=1))
        
        # Calculate the delta (acceleration proxy)
        velocity_delta = abs(current_velocity_mag - self._prev_velocity_mag)
        self._prev_velocity_mag = current_velocity_mag

        # Update movement state
        was_moving = self.is_moving
        self.is_moving = current_velocity_mag > self.threshold
        
        # Trigger on state change (Start/Stop) or significant delta
        if was_moving != self.is_moving:
            return True
        
        return velocity_delta > (self.threshold * 2) # Significant shift within motion
