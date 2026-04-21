# Sign-Verse Production Dataset V1

## Overview
**Sign-Verse Production Dataset V1** is a high-fidelity collection of 3D kinematic motion data extracted from 10 diverse categories of human performance. This dataset is designed for training robotic intelligence controllers, motion retargeting models, and full-body humanoid simulations.

## Dataset Statistics
- **Total Videos**: 10
- **Total Categories**: 10
- **Sampling Rate**: 2.0 FPS (Kinematic States)
- **Total Frames**: ~6,000+ Synchronized Data Points
- **Resolution**: 640x360 (Source Reference)

## Directory Structure
- `/kinematics`: Optimized training tensors (`.npy`) and telemetry spreadsheets (`.csv`).
- `/simulation`: 3D skeletal configurations (`.json`) for Isaac Sim / PhysX.
- `/animation`: Industry-standard motion capture files (`.bvh`) and web-ready animations (`gltf`).
- `/previews`: Annotated MP4 videos showing the 3D skeletal overlay on raw footage.
- `/metadata`: Individual session manifests for data provenance.

## Categories
1.  **Acting**: Dramatic performances and camera-facing expressions.
2.  **Art**: Specialized movements (e.g., Mime, performance art).
3.  **Cooking**: Fine-motor hand-eye coordination sequences.
4.  **Dance**: Complex choreography and rhythmic motion.
5.  **Martial Arts**: high-velocity combat patterns (Staff/Stick training).
6.  **Parkour**: Dynamic locomotion and agility (Tricking masterclass).
7.  **Speech**: Public speaking and hand-gesture communication.
8.  **Sports**: Athletic explosive power and speed drills.
9.  **Workout**: Repetitive fitness and mobility sequences.
10. **Yoga**: Low-velocity balance and flexibility flow.

## Usage
Refer to `index.json` for a programmatic map of all items and their file paths. All paths in the index are relative to the dataset root.
