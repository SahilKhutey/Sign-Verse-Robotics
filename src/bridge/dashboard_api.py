from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import List, Dict, Any

router = APIRouter()

class TelemetryBroadcaster:
    """
    Manages high-frequency WebSocket broadcasting for the Dashboard.
    Optimized for 30FPS telemetry + sampled video status.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        message = json.dumps(data)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

broadcaster = TelemetryBroadcaster()

@router.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)

@router.post("/control/capture/{action}")
async def control_capture(action: str):
    """Start/Stop recording and capture pipelines."""
    # Logic to trigger capture engine
    return {"status": f"Capture {action}ed"}

@router.post("/control/sim/{action}")
async def control_sim(action: str):
    """Start/Stop or trigger disturbances in the simulation."""
    return {"status": f"Simulation {action}ed"}
