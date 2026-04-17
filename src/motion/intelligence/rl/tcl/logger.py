import json
import time
import threading
from typing import Dict, Any, List

class ExplainabilityLogger:
    """
    Audit-grade logger for Sign-Verse Decisions.
    Uses chunked buffering to minimize disk I/O in high-frequency loops.
    """
    def __init__(self, log_path: str = "logs/decisions.json", chunk_interval: int = 5):
        self.log_path = log_path
        self.buffer: List[Dict[str, Any]] = []
        self.interval = chunk_interval
        self.lock = threading.Lock()
        self.last_flush = time.time()
        
    def log(self, decision: Dict[str, Any]):
        """
        Decision schema: {time, state, action, confidence, safety_override}
        """
        with self.lock:
            self.buffer.append({
                "t": time.time(),
                **decision
            })
            
        # Periodic flush check (non-blocking)
        if (time.time() - self.last_flush) >= self.interval:
            threading.Thread(target=self._flush).start()

    def _flush(self):
        """Writes current buffer to disk and clears list."""
        if not self.buffer:
            return
            
        with self.lock:
            data_to_write = list(self.buffer)
            self.buffer = []
            self.last_flush = time.time()
            
        try:
            with open(self.log_path, "a") as f:
                for entry in data_to_write:
                    f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"❌ TCL Logging Error: {e}")

    def shutdown(self):
        """Final flush on cleanup."""
        self._flush()
