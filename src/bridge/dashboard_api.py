from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

# Global reference to orchestrator, initialized in main.py
orchestrator = None

def init_orchestrator(ord_instance):
    global orchestrator
    orchestrator = ord_instance

@router.post("/control/capture/toggle")
async def toggle_capture():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    state = orchestrator.toggle_recording()
    return {"status": "success", "is_recording": state}

@router.post("/control/sim/toggle")
async def toggle_sim():
    # Placeholder for simulation engine toggle
    return {"status": "success", "simulation_active": True}

@router.post("/control/annotations/toggle")
async def toggle_annotations():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    orchestrator.show_annotations = not orchestrator.show_annotations
    return {"status": "success", "show_annotations": orchestrator.show_annotations}

@router.post("/control/emergency/stop")
async def emergency_stop():
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    result = orchestrator.emergency_stop()
    return result

@router.get("/status")
async def get_system_status():
    if not orchestrator:
        return {"status": "offline"}
    return orchestrator.get_health_report()
