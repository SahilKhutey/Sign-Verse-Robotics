from typing import List, Dict, Any

class AlertEngine:
    """
    Threshold-based intelligence for detecting anomalies in the ingestion stream.
    Identifies high-latency, low-fps, or memory-pressure conditions.
    """
    def __init__(self, 
                 latency_threshold_ms: float = 200.0, 
                 fps_threshold: float = 10.0):
        self.latency_threshold = latency_threshold_ms
        self.fps_threshold = fps_threshold

    def check(self, metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Analyzes the metrics snapshot and returns a list of active alerts.
        """
        alerts = []
        
        for source_id, data in metrics.items():
            # 1. Latency Check
            if data.get("latency_ms", 0) > self.latency_threshold:
                alerts.append(f"CRITICAL: High Latency on {source_id} ({data['latency_ms']}ms)")
            
            # 2. FPS Check
            if data.get("fps", 0) < self.fps_threshold and data.get("total_frames", 0) > 100:
                alerts.append(f"WARNING: Low FPS on {source_id} ({data['fps']} FPS)")

        return alerts
