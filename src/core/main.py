import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, StreamingResponse, FileResponse
import cv2
import numpy as np
import os
import shutil
import uuid
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import UploadFile, File
from src.core.orchestrator import Orchestrator
from src.core.auto_youtube_pipeline import AutoYouTubePipelineManager, DEFAULT_CATEGORIES
from src.ingestion.schemas import SourceType
from src.ingestion.adapters.youtube import YouTubeAdapter
from src.bridge.dashboard_api import router as dashboard_router, init_orchestrator


def _session_dir(name: str) -> str:
    return os.path.join("datasets", name)


def _session_file(name: str, filename: str) -> str:
    return os.path.join(_session_dir(name), filename)


def _batch_root() -> str:
    return os.path.join("datasets", "batches")


def _batch_dir(batch_id: str) -> str:
    return os.path.join(_batch_root(), batch_id)


def _batch_file(batch_id: str, filename: str) -> str:
    return os.path.join(_batch_dir(batch_id), filename)


def _read_json_file(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl_file(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _build_session_summary(name: str):
    session_path = _session_dir(name)
    if not os.path.isdir(session_path):
        return None

    workflow_summary = _read_json_file(_session_file(name, "workflow_summary.json")) or {}
    metadata = _read_jsonl_file(_session_file(name, "metadata.jsonl"))
    motion_frames = _read_jsonl_file(_session_file(name, "motion_states.jsonl"))
    training_csv = _session_file(name, "training_set.csv")
    training_npy = _session_file(name, "training_set.npy")
    annotated_preview = _session_file(name, "annotated_preview.mp4")

    first_ts = metadata[0]["timestamp"] if metadata else (motion_frames[0]["timestamp"] if motion_frames else 0.0)
    last_ts = metadata[-1]["timestamp"] if metadata else (motion_frames[-1]["timestamp"] if motion_frames else 0.0)
    duration_s = max(0.0, last_ts - first_ts)
    artifact_files = [
        "annotated_preview.mp4",
        "session_archive.mp4",
        "simulation_2d.json",
        "simulation_3d.json",
        "retargeted_motion.json",
        "gltf_animation.json",
        "blender_export.bvh",
        "training_set.npy",
        "training_set.csv",
    ]

    return {
        "name": name,
        "path": session_path,
        "frame_count": len(metadata),
        "motion_frame_count": len(motion_frames),
        "duration_s": duration_s,
        "processed_frames": workflow_summary.get("processed_frames", len(metadata)),
        "tracked_frames": workflow_summary.get("tracked_frames", len(motion_frames)),
        "effective_fps": workflow_summary.get("effective_fps"),
        "source_video": workflow_summary.get("source_video"),
        "chunk_frames": workflow_summary.get("chunk_frames"),
        "has_thumbnail": os.path.exists(_session_file(name, "thumbnail.jpg")),
        "has_preview": os.path.exists(annotated_preview),
        "has_training_export": os.path.exists(training_npy) and os.path.exists(training_csv),
        "artifact_files": [filename for filename in artifact_files if os.path.exists(_session_file(name, filename))],
        "workflow_summary": workflow_summary,
    }


def _build_batch_summary(batch_id: str):
    batch_path = _batch_dir(batch_id)
    manifest = _read_json_file(_batch_file(batch_id, "batch_manifest.json"))
    if manifest is None:
        return None

    videos = manifest.get("videos", [])
    completed = len(videos)
    verified = sum(1 for video in videos if video.get("workflow", {}).get("verification_ok"))
    processed_total = sum(int(video.get("summary", {}).get("processed_frames", 0)) for video in videos)
    tracked_total = sum(int(video.get("summary", {}).get("tracked_frames", 0)) for video in videos)

    return {
        "batch_id": batch_id,
        "path": batch_path,
        "video_folder": manifest.get("video_folder"),
        "video_count": manifest.get("video_count", completed),
        "completed_count": completed,
        "verified_count": verified,
        "processed_frames_total": processed_total,
        "tracked_frames_total": tracked_total,
        "artifacts": {
            "manifest": os.path.exists(_batch_file(batch_id, "batch_manifest.json")),
            "report_csv": os.path.exists(_batch_file(batch_id, "consolidated_report.csv")),
            "report_json": os.path.exists(_batch_file(batch_id, "consolidated_report.json")),
        },
        "videos": videos,
    }
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the async processing loop in the background
    task = asyncio.create_task(orchestrator.process_loop())
    yield
    # Cleanup logic if necessary
    orchestrator.is_running = False
    await task

orchestrator = Orchestrator()
auto_youtube_pipeline = AutoYouTubePipelineManager()
app = FastAPI(title="Sign-Verse Robotics API", version="2.0.0", lifespan=lifespan)

# Enable CORS for the Dashboard (Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_orchestrator(orchestrator)
app.include_router(dashboard_router, prefix="/api/v1")

@app.get("/")
async def root():
    return RedirectResponse(url="/health")

class ProcessRequest(BaseModel):
    source_uri: str
    source_type: SourceType

class KinematicsConfigRequest(BaseModel):
    smoothing: float = 0.4
    damping: float = 0.05


class AutoYouTubePipelineRequest(BaseModel):
    categories: list[str] = DEFAULT_CATEGORIES
    results_per_category: int = 1
    sample_fps: float | None = None
    chunk_frames: int = 90

@app.post("/ingest/start")
async def start_ingestion(request: ProcessRequest):
    """Start a new ingestion stream."""
    try:
        source_uri = request.source_uri
        # Resolve integer index for hardware cameras
        if request.source_type == SourceType.CAMERA:
            try:
                source_uri = int(request.source_uri)
            except ValueError:
                pass
        
        adapter_id = orchestrator.start_ingestion(request.source_type, source_uri)
        return {"status": "started", "adapter_id": adapter_id, "source_type": request.source_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/youtube/auto/start")
async def start_auto_youtube_pipeline(request: AutoYouTubePipelineRequest):
    """Search, download, and process category-based YouTube videos as a batch job."""
    try:
        job = auto_youtube_pipeline.start_job(
            categories=request.categories,
            results_per_category=request.results_per_category,
            sample_fps=request.sample_fps,
            chunk_frames=request.chunk_frames,
        )
        return {"status": "started", "job": job}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/youtube/auto/status")
async def get_auto_youtube_pipeline_status(job_id: str | None = None):
    """Return latest or specific auto-youtube pipeline job status."""
    try:
        job = auto_youtube_pipeline.get_job(job_id) if job_id else auto_youtube_pipeline.get_latest_job()
        if job is None:
            return {"status": "idle", "job": None}
        return {"status": "ok", "job": job}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/youtube/auto/jobs")
async def list_auto_youtube_pipeline_jobs(limit: int = 10):
    """Return recent auto-youtube pipeline jobs for dashboard history."""
    try:
        return {"jobs": auto_youtube_pipeline.list_jobs(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/stop")
async def stop_ingestion():
    """Stop all active ingestion adapters."""
    try:
        orchestrator.stop_ingestion()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingest/search")
async def search_youtube(query: str):
    """Returns top 5 YouTube results with thumbnails and verbose error handling."""
    try:
        results = YouTubeAdapter.search(query)
        if not results:
            print(f"[Search Debug] No results found for query: {query}")
        return {"results": results, "status": "success"}
    except Exception as e:
        print(f"[Search Debug] Fatal Backend Error: {e}")
        return {"results": [], "status": "error", "message": str(e)}

@app.get("/hardware/cameras")
async def list_available_cameras():
    """Probe hardware for available camera indices (0-5) using multiple backends."""
    available = []
    # Try DirectShow (DSHOW) first as it's most compatible on Windows
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
    found_indices = set()
    
    for backend in backends:
        for i in range(5):
            if i in found_indices: continue
            cap = cv2.VideoCapture(i, backend) if backend is not None else cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append({"index": i, "name": f"Hardware Camera {i}", "backend": "DSHOW" if backend == cv2.CAP_DSHOW else "MSMF"})
                    found_indices.add(i)
                cap.release()
    return {"cameras": available}

@app.post("/ingest/upload")
async def upload_image(file: UploadFile = File(...)):
    """Saves an image to temp storage and returns the local path."""
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "uploaded", "local_path": os.path.abspath(file_path)}

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

@app.post("/dataset/export")
async def export_dataset(name: str):
    """Batch processes a session into Training tensors and CSV analysis."""
    from src.storage.training_exporter import TrainingExporter
    try:
        exporter = TrainingExporter()
        # Look for the session in the datasets directory
        session_path = os.path.join("datasets", name)
        success = exporter.process_session(session_path)
        if success:
            return {"status": "export_complete", "formats": ["npy", "csv"]}
        else:
            return {"status": "error", "message": "Session not found or invalid"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/intelligence/config")
def update_intelligence(threshold: float):
    orchestrator.update_intelligence_config(threshold)
    return {"status": "Threshold updated", "new_threshold": threshold}

@app.post("/control/kinematics/config")
async def update_kinematics(config: KinematicsConfigRequest | None = None, smoothing: float = 0.4, damping: float = 0.05):
    """Updates the JointMapper heuristics for real-time retargeting."""
    try:
        if config is not None:
            smoothing = config.smoothing
            damping = config.damping
        orchestrator.joint_mapper.update_config({
            "smoothing_factor": smoothing,
            "damping": damping
        })
        return {"status": "success", "config": {"smoothing": smoothing, "damping": damping}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/training/stats")
async def get_training_stats():
    """Returns dataset size and latest model metrics."""
    return orchestrator.metrics.training_metrics

@app.post("/training/launch")
async def launch_training(epochs: int = 10):
    """Manually triggers an Active Learning sweep."""
    if orchestrator.is_training:
        return {"status": "error", "message": "Training already in progress."}
    
    asyncio.create_task(orchestrator.trigger_training(epochs))
    return {"status": "success", "message": f"Launched training for {epochs} epochs."}

@app.post("/control/calibrate")
async def calibrate_system():
    """Resets all internal and external simulator states."""
    try:
        result = await orchestrator.calibrate()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/bridge/{bridge_name}/toggle")
async def toggle_bridge(bridge_name: str, enabled: bool):
    """Dynamically enables/disables simulation bridges."""
    if bridge_name == "blender":
        orchestrator.bridge_status["blender_enabled"] = enabled
    elif bridge_name == "isaac":
        orchestrator.bridge_status["isaac_enabled"] = enabled
    else:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return {"status": "success", "bridge": bridge_name, "enabled": enabled}

@app.post("/intelligence/load_model")
async def load_model_weights(path: str):
    """Hot-swaps model weights for real-time behavioral switching."""
    success = orchestrator.intelligence.load_model_weights(path)
    if success:
        return {"status": "success", "message": f"Loaded weights from {path}"}
    else:
        raise HTTPException(status_code=404, detail=f"Model weights not found at {path}")

@app.get("/dataset/sessions")
async def list_sessions():
    """List all available recorded sessions."""
    try:
        datasets_dir = "datasets"
        if not os.path.exists(datasets_dir):
            return {"sessions": []}
        sessions = [d for d in os.listdir(datasets_dir) if os.path.isdir(os.path.join(datasets_dir, d))]
        return {"sessions": sorted(sessions, reverse=True)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/batches")
async def list_batches():
    """List stored batch workflow runs for dashboard browsing."""
    try:
        root = _batch_root()
        if not os.path.exists(root):
            return {"batches": []}
        batch_ids = sorted(
            [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))],
            reverse=True,
        )
        batches = []
        for batch_id in batch_ids:
            summary = _build_batch_summary(batch_id)
            if summary is not None:
                batches.append(summary)
        return {"batches": batches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/batch/{batch_id}")
async def get_batch(batch_id: str):
    """Return the full stored batch manifest and summary."""
    try:
        summary = _build_batch_summary(batch_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="Batch not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/batch/{batch_id}/artifact/{artifact_name}")
async def get_batch_artifact(batch_id: str, artifact_name: str):
    """Serve batch-level manifest and consolidated report artifacts."""
    allowed_files = {
        "manifest": "batch_manifest.json",
        "report_csv": "consolidated_report.csv",
        "report_json": "consolidated_report.json",
    }
    filename = allowed_files.get(artifact_name)
    if filename is None:
        raise HTTPException(status_code=404, detail="Batch artifact not found")
    path = _batch_file(batch_id, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Batch artifact missing")
    return FileResponse(path)


@app.get("/dataset/session/{name}/summary")
async def get_session_summary(name: str):
    """Return a dashboard-friendly summary of a processed session."""
    try:
        summary = _build_session_summary(name)
        if summary is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dataset/session/{name}/thumbnail")
async def get_session_thumbnail(name: str):
    """Serve the thumbnail preview for a specific session."""
    thumbnail_path = os.path.join("datasets", name, "thumbnail.jpg")
    if not os.path.exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(thumbnail_path)

@app.get("/dataset/session/{name}/motion")
async def get_session_motion(name: str):
    """Retrieve kinematic frame data for a specific session."""
    try:
        file_path = _session_file(name, "motion_states.jsonl")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Session motion data not found")
        
        frames = []
        with open(file_path, "r") as f:
            for line in f:
                frames.append(json.loads(line))
        return {"frames": frames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/session/{name}/simulation/{mode}")
async def get_session_simulation(name: str, mode: str):
    """Retrieve exported playback artifacts for 2D/3D simulation and retargeting."""
    try:
        filename_map = {
            "2d": "simulation_2d.json",
            "3d": "simulation_3d.json",
            "retarget": "retargeted_motion.json",
            "gltf": "gltf_animation.json",
        }
        if mode not in filename_map:
            raise HTTPException(status_code=404, detail="Simulation artifact not found")
        payload = _read_json_file(_session_file(name, filename_map[mode]))
        if payload is None:
            raise HTTPException(status_code=404, detail="Simulation artifact missing")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/session/{name}/artifact/{artifact_name}")
async def get_session_artifact(name: str, artifact_name: str):
    """Serve generated preview and export artifacts from a processed session."""
    allowed_files = {
        "preview": "annotated_preview.mp4",
        "archive": "session_archive.mp4",
        "thumbnail": "thumbnail.jpg",
        "bvh": "blender_export.bvh",
        "csv": "training_set.csv",
        "npy": "training_set.npy",
    }
    filename = allowed_files.get(artifact_name)
    if filename is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = _session_file(name, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Artifact missing")
    return FileResponse(path)

@app.get("/metrics")
async def get_metrics():
    """Returns the current health and metrics snapshot."""
    return orchestrator.get_health_report()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket Command Center: Streams real-time telemetry to the dashboard.
    Frequency boosted to 20Hz for Dashboard v1.0.
    """
    await websocket.accept()
    print("[WebSocket] Dashboard connected")
    try:
        while True:
            # Broadcast the consolidated health report
            report = orchestrator.get_health_report()
            await websocket.send_json(report)
            await asyncio.sleep(0.05) # 20Hz refresh rate
    except WebSocketDisconnect:
        print("[WebSocket] Dashboard disconnected")
    except Exception as e:
        print(f"[WebSocket Error] {e}")

@app.get("/health")
async def health_check():
    return orchestrator.get_health_report()

@app.get("/video_feed")
async def video_feed():
    """
    RTSP-style MJPEG stream delivering live annotated computer vision feed.
    """
    def placeholder_frame(message: str) -> bytes:
        canvas = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.putText(canvas, "SIGN-VERSE LIVE FEED", (120, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, message, (120, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        ok, buffer = cv2.imencode('.jpg', canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return buffer.tobytes() if ok else b""

    async def frame_stream():
        while True:
            frame = orchestrator.latest_annotated_frame
            if frame is not None:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # High-speed MJPEG encoding with optimized quality (80)
                _, buffer = cv2.imencode('.jpg', frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_bytes = buffer.tobytes()
            else:
                frame_bytes = placeholder_frame("Awaiting source frames...")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.03) # ~30FPS limit
            
    return StreamingResponse(frame_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
