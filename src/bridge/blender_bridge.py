import asyncio
import json
from typing import Set, Dict
from fastapi import WebSocket, WebSocketDisconnect

class BlenderLiveLink:
    """
    Dedicated WebSocket bridge for Blender real-time animation.
    Broadcasts JointState data optimized for Blender's Python API.
    """
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[BlenderBridge] Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[BlenderBridge] Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, joint_angles: Dict[str, float]):
        """
        Sends robotic joint angles to all connected Blender instances.
        Data format is flat for high-speed parsing in Blender script.
        """
        if not self.active_connections:
            return

        message = {
            "type": "joint_update",
            "data": joint_angles
        }
        
        # Async broadcast
        await asyncio.gather(
            *[connection.send_json(message) for connection in self.active_connections],
            return_exceptions=True
        )

    async def reset(self):
        """Notifies Blender to reset the armature to neutral pose."""
        if not self.active_connections:
            return
        message = {"type": "reset", "data": {}}
        await asyncio.gather(
            *[connection.send_json(message) for connection in self.active_connections],
            return_exceptions=True
        )

# Global singleton
blender_bridge = BlenderLiveLink()
