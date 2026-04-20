import json
import os
import threading
import queue
from typing import Optional
import numpy as np
from src.motion.core.state import MotionState

class MotionStateRecorder:
    """
    Dedicated recorder for stabilized human motion state (S_t).
    Enables replay of the mathematical skeleton without re-running perception.
    """
    def __init__(self):
        self.file = None
        self.queue = queue.Queue(maxsize=1000)
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self, session_path: str):
        self.file = open(os.path.join(session_path, "motion_states.jsonl"), "a")
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        while self.running or not self.queue.empty():
            try:
                state = self.queue.get(timeout=0.5)
                self._persist(state)
                self.queue.task_done()
            except queue.Empty:
                continue

    def _persist(self, state: MotionState):
        entry = {
            "timestamp": state.timestamp,
            "position": state.position.tolist() if isinstance(state.position, np.ndarray) else state.position,
            "velocity": state.velocity.tolist() if isinstance(state.velocity, np.ndarray) else state.velocity,
            "confidence": state.confidence,
            "source_id": state.source_id,
            "metadata": state.metadata or {}
        }
        
        # Add joints if available
        if hasattr(state, 'joints') and state.joints is not None:
            entry["joints"] = state.joints.tolist() if isinstance(state.joints, np.ndarray) else state.joints

        self.file.write(json.dumps(entry) + "\n")
        self.file.flush()

    def record(self, state: MotionState):
        if self.running:
            self.queue.put(state)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.file:
            self.file.close()
