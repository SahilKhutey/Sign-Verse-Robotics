import socket
import json
from typing import Dict, Any

class IsaacUDPBridge:
    """
    High-speed UDP Bridge for NVIDIA Isaac Sim.
    Broadcasts JointState data as minimized JSON packets for the Omniverse Python API.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 5005):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[IsaacBridge] UDP Stream initialized on {self.host}:{self.port}")

    def broadcast(self, joint_angles: Dict[str, float]):
        """
        Sends robotic joint angles via UDP packet.
        Low-latency, fire-and-forget.
        """
        try:
            # Filter metadata and just send pure angles
            payload = {k: round(v, 4) for k, v in joint_angles.items() if k not in ["timestamp", "status"]}
            message = json.dumps(payload).encode('utf-8')
            self.sock.sendto(message, (self.host, self.port))
        except Exception as e:
            print(f"[IsaacBridge] UDP Send Error: {e}")

    def reset(self):
        """Broadcasts a reset command to Isaac Sim listeners."""
        self.broadcast({"cmd": "RESET", "joints": {}})

# Global singleton
isaac_bridge = IsaacUDPBridge()
