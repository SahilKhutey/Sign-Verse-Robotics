import psutil
import os
from typing import Tuple

class MemoryGuard:
    """
    Proactive system watchdog to prevent queue explosion or memory leaks.
    Monitors process RAM and signals emergency flushes if thresholds are hit.
    """
    def __init__(self, threshold_mb: float = 1500.0):
        """
        :param threshold_mb: Max allowed RSS memory before triggering safety measures.
        """
        self.threshold = threshold_mb
        self.process = psutil.Process(os.getpid())

    def check(self) -> Tuple[bool, float]:
        """
        Returns (is_safe, current_mem_mb).
        """
        try:
            mem_info = self.process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            
            if mem_mb > self.threshold:
                return False, mem_mb
                
            return True, mem_mb
        except Exception as e:
            print(f"[MemoryGuard Error] {e}")
            return True, 0.0

    def trigger_emergency_flush(self, bus):
        """
        Policy: Flush 20% of the oldest frames from the StreamBus 
        to recover memory immediately.
        """
        # Note: The actual implementation of flush will depend on the StreamBus API.
        # Here we conceptually signal or call a specific bus method.
        pass
