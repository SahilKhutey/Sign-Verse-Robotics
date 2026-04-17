from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from src.core.orchestrator import Orchestrator
from src.ingestion.schemas import SourceType, MotionSequence
import uvicorn
import asyncio
import json

app = FastAPI(title="Sign-Verse Robotics API", version="2.0.0")
orchestrator = Orchestrator()

class ProcessRequest(BaseModel):
    source_uri: str
    source_type: SourceType

@app.on_event("startup")
async def startup_event():
    # Start the async processing loop in the background
    asyncio.create_task(orchestrator.process_loop())

@app.post("/ingest/start")
async def start_ingestion(request: ProcessRequest):
    """Start a new ingestion stream."""
    try:
        adapter_id = orchestrator.start_ingestion(request.source_type, request.source_uri)
        return {"status": "started", "adapter_id": adapter_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dataset/start")
async def start_dataset_session(name: str):
    """Initialize a production-grade recording session."""
    try:
        orchestrator.start_recording(name)
        return {"status": "recording_started", "session_name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dataset/stop")
async def stop_dataset_session():
    """Finalize the current recording session and index metadata."""
    try:
        orchestrator.stop_recording()
        return {"status": "recording_stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/intelligence/config")
def update_intelligence(threshold: float):
    orchestrator.update_intelligence_config(threshold)
    return {"status": "Threshold updated", "new_threshold": threshold}

@app.get("/metrics")
async def get_metrics():
    """Returns the current health and metrics snapshot."""
    return orchestrator.get_health_report()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket Command Center: Streams real-time telemetry to the dashboard.
    """
    await websocket.accept()
    print("[WebSocket] Dashboard connected")
    try:
        while True:
            # Broadcast the consolidated health report
            report = orchestrator.get_health_report()
            await websocket.send_json(report)
            await asyncio.sleep(0.5) # 2Hz refresh rate
    except WebSocketDisconnect:
        print("[WebSocket] Dashboard disconnected")
    except Exception as e:
        print(f"[WebSocket Error] {e}")

@app.get("/health")
async def health_check():
    return orchestrator.get_health_report()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
