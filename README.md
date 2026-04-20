# Sign-Verse Robotics: The Sovereign Humanoid Intelligence Platform
![Platform Version](https://img.shields.io/badge/Version-5.2_Sovereign-cyan?style=for-the-badge&logo=robotics)
![Stability Health](https://img.shields.io/badge/Stability-100%25_Balanced-emerald?style=for-the-badge)
![Data Synthesis](https://img.shields.io/badge/Data_Synth-Automated-orange?style=for-the-badge)

Sign-Verse Robotics is a **frontier-grade, AI-native embodied intelligence system**. It bridges the gap between high-level human social intent and precise robotic manifestation. The platform is designed for mission-critical social interaction, dynamic locomotion, and human-in-the-loop safety.

## 🏗️ Core Architecture
The system operates on a continuous loop of high-frequency perception, cognitive understanding, and physical manifestation.

```mermaid
graph TD
    subgraph INGESTION[0. Auto-Ingestion]
        YT[YouTube API / Search] --> ADAPT[YouTube Adapter]
        ADAPT --> VRAW[Raw Video]
    end

    subgraph PERCEPTION[1. Perception]
        direction TB
        VRAW --> MP[MediaPipe/YOLO Fusion]
        MP --> SKEL[3D Skeletal Reconstruction]
    end

    subgraph BRAIN[2. Cognitive Brain]
        direction TB
        SKEL --> MMTE[MMTE: Multimodal Transformer]
        MMTE --> TIE[TIE: Intent Engine]
        TIE --> RLAP[RLAP: Action Policy]
    end

    subgraph EMBODIMENT[3. Physical Embodiment]
        direction TB
        RLAP --> PRS[PRS: Robotics Stack]
        PRS --> WBMPC[WBMPC: Contact Locomotion]
    end

    INGESTION --> PERCEPTION
    PERCEPTION --> BRAIN
    BRAIN --> EMBODIMENT
    EMBODIMENT -- Telemetry --> DASH[Control Tower Dashboard]
    DASH -- Manual Override --> EMBODIMENT
```

## 🚀 Key Milestones (V1.0 - V5.2)
The project evolved through **32 major implementation phases**, achieving state-of-the-art results in:
*   **MMTE (Multimodal Transformer Engine)**: Unified 345D tokenization of motion, face, and spatial context.
*   **TIE V2 (Intent Transformer)**: Sequence-aware intent classification.
*   **RL-SDS (Safety & Deployment)**: Uncertainty-aware exploration and proximity guardrails.
*   **WBMPC (Whole-Body MPC)**: High-performance C++ solver for contact-aware locomotion and footstep planning.
*   **Auto YouTube Pipeline (V5.2)**: Automated searching, downloading, and retargeting of motion data from YouTube categories (Workout, Dance, etc.) to build massive synthetic datasets.
*   **Control Tower Dashboard**: Next.js/Three.js cockpit for real-time 3D telemetry and batch job orchestration.

## 📂 System Structure
```text
src/
├── core/            # System Orchestration & Auto Pipelines
├── motion/          # Cognitive & Intent Pipelines
├── robotics/        # Kinematics, WBC, MPC, and WBMPC Solver
├── bridge/          # Dashboard APIs & Telemetry
└── perception/      # MediaPipe & YOLO Tracking
scripts/             # Batch Processing & Workflow Tools
dashboard/           # Next.js Command Center (Control Tower)
docs/                # Technical Reports & Handbooks
```

## 🛠️ Technology Stack
*   **Backend**: Python, FastAPI, WebSocket (30Hz), NumPy Vectorization.
*   **Control**: C++ (WBMPC Optimization Core), Numerical Jacobian IK.
*   **AI**: PyTorch, Transformers, Reinforcement Learning (PPO).
*   **Frontend**: Next.js, Three.js (WebGL), TailwindCSS, Zustand.

## 🛡️ Safety & Reliability
Sign-Verse is built for **Physical Sovereignty**. The system features a multi-layered safety stack:
1.  **Exploration Guardrails**: Managed ε-greedy exploration for stable online learning.
2.  **Stability Thresholds**: Automatic intent suppression if ZMP health drops below 80%.
3.  **Human Override**: Latching control system allowing operators to seize hardware control in <5ms.

---
**Developed by Sahil Khutey**
*Platform Status: Sovereign. Ready for World-Level Deployment.*
