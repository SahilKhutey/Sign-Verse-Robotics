import socket
import json
import time
from typing import Dict, Any

class RobotPolicyExporter:
    """
    Transforms stabilized actions into hardware-ready policy packets.
    Ready for deployment to physical humanoid control units.
    """
    def export_command(self, joints_mapped: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": "1.2",
            "timestamp": time.time(),
            "priority": meta.get("priority", 0.5),
            "mode": meta.get("mode", "POSITION_CONTROL"),
            "joints": joints_mapped,
            "safety_status": meta.get("safety_clip_active", False)
        }

class StreamExporter:
    """
    High-speed UDP Broadcaster for multi-observer synchronization.
    Sends real-time joint and state data to Blender, Unreal, and Robot units.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 9001):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (host, port)

    def broadcast(self, payload: Dict[str, Any]):
        """
        Sends a single state update frame.
        """
        try:
            msg = json.dumps(payload).encode('utf-8')
            self.sock.sendto(msg, self.target)
        except Exception as e:
            print(f"📡 Stream Error: {e}")
            
    def close(self):
        self.sock.close()
