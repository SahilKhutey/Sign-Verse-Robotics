# Sign-Verse Robotics: Technical Handbook (V5.2)

This handbook provides production-grade guidance for deploying, configuring, and scaling the Sign-Verse embodied intelligence platform.

---

## 🏗️ 1. Architecture Deep-Dive

### Perception Fusion Layer
The system utilizes a dual-path perception strategy:
- **Live Stream**: Optimized for RTSP/Studio capture (30Hz).
- **Offline Batch**: Utilizes a sampling engine to process video files at variable FPS, recycling the perception stack every ~90 frames to maintain stability.

### The Cognitive Transformer (MMTE)
The Multimodal Transformer Engine unifies:
1. **Pose (33 Landmarks)**: MediaPipe-based spatial skeletal data.
2. **Face (468 Landmarks)**: Fine-grained affective state detection.
3. **Hands (21 Landmarks)**: Dexterous gesture recognition.
All are tokenized into a 345D vector for intent classification.

### WBMPC Solver (The C++ Core)
The Whole-Body Model Predictive Control solver is a high-performance C++ implementation using quadratic programming to optimize:
- **Balance (ZMP/CoM)**
- **Contact Forces**
- **Footstep Timings**

---

## 🛠️ 2. Production Setup

### Environment Prerequisites
- **Python**: 3.10+ (recommend 3.12 for performance).
- **CUDA**: 11.8+ (for YOLO/Transformer acceleration).
- **C++ Compiler**: MSVC (Windows) or GCC (Linux) for solver compilation.

### Initializing the Workspace
```powershell
# Install core dependencies
pip install -r requirements.txt

# Compile the WBMPC Solver (Windows)
.\src\robotics\wbmpc\solver\build_solver.bat
```

### Starting the Control Tower
```powershell
# Launch the backend and dashboard bridge
python scripts/mission_control.py

# In a separate shell, start the Next.js Dashboard
cd dashboard
npm run dev
```

---

## 🚀 3. Automated Data Synthesis

The V5.2 update introduces the **Automated Workflow Engine**.

### Running a YouTube Sync
You can trigger a massive data harvesting job via the `AutoYouTubePipelineManager`:
```python
from src.core.auto_youtube_pipeline import AutoYouTubePipelineManager

manager = AutoYouTubePipelineManager()
job = manager.start_job(
    categories=["yoga", "manual_labor"],
    results_per_category=5,
    sample_fps=3.0
)
print(f"Started Job: {job['job_id']}")
```

### Batch Processing Scripts
- `scripts/run_video_batch.py`: Processes a whole directory of videos.
- `scripts/generate_batch_report.py`: Generates consolidated CSV/JSON reports of tracking performance.

---

## 🛡️ 4. Maintenance & Safety

### Telemetry Auditing
All sessions are archived in `datasets/`. While raw frames/videos are `.gitignored`, the `session_archive.mp4` and `retargeted_motion.json` provide a full forensic trail of the robot's logic.

### Safety Guardrails
1. **Proximity Shutdown**: The system automatically halts if a human subject is detected within the "Critical Collision Zone" (<0.5m) and social intent is aggressive.
2. **ZMP Health**: If the balance health score drops below 0.82, the system transitions to a "Safe Crouch" state.

---
*Document Version: 5.2.0-STABLE*  
*Lead Architect: Sahil Khutey*
