import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.orchestrator import Orchestrator
from src.export.formats.exporters import BVHExporter, GLTFExporter
from src.ingestion.schemas import SourceType
from src.motion.kinematics.models.human import HumanSkeleton
from src.storage.training_exporter import TrainingExporter


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_json_ready(payload), handle, indent=2)


def _joint_2d_payload(subject) -> List[Dict[str, float]]:
    if not subject.pose or not subject.pose.skeleton:
        return []
    return [
        {
            "x": float(joint.x),
            "y": float(joint.y),
            "z": float(joint.z),
            "visibility": float(joint.visibility),
        }
        for joint in subject.pose.skeleton
    ]


def _collect_gltf_tracks(actions: np.ndarray, timestamps: np.ndarray) -> List[Dict[str, Any]]:
    tracks: List[Dict[str, Any]] = []
    if actions.ndim != 2 or actions.shape[0] == 0:
        return tracks
    for joint_index in range(actions.shape[1]):
        tracks.append(
            {
                "path": f"robot_joint_{joint_index}",
                "times": timestamps.tolist(),
                "values": actions[:, joint_index].tolist(),
            }
        )
    return tracks


def _select_primary_subject(subjects) -> Optional[Any]:
    if not subjects:
        return None
    return max(
        subjects,
        key=lambda subject: (
            (subject.bbox[2] - subject.bbox[0]) * (subject.bbox[3] - subject.bbox[1]),
            subject.confidence,
        ),
    )


def _new_orchestrator() -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.robot_bridge.dispatch = lambda _joint_angles: None
    orchestrator.bridge_status["isaac_enabled"] = False
    orchestrator.bridge_status["blender_enabled"] = False
    orchestrator.perception.face_interval = 6
    orchestrator.perception.detection_interval = 4
    orchestrator.show_annotations = True
    return orchestrator


def _create_session(session_name: str) -> str:
    session_id = f"{session_name}_{int(time.time())}"
    session_path = os.path.join("datasets", session_id)
    os.makedirs(os.path.join(session_path, "frames"), exist_ok=True)
    return session_path


def _write_frame_packet(
    session_path: str,
    packet,
    metadata_handle,
    video_writer,
    thumbnail_written: bool,
) -> bool:
    frame_filename = f"frame_{packet.frame_index:06d}.jpg"
    frame_path = os.path.join(session_path, "frames", frame_filename)
    cv2.imwrite(frame_path, packet.frame_normalized)
    video_writer.write(packet.frame_normalized)

    if not thumbnail_written:
        thumbnail = cv2.resize(packet.frame_normalized, (320, 320))
        cv2.imwrite(os.path.join(session_path, "thumbnail.jpg"), thumbnail)
        thumbnail_written = True

    metadata_handle.write(
        json.dumps(
            {
                "frame_index": packet.frame_index,
                "timestamp": packet.timestamp,
                "source_id": packet.source_id,
                "sync_id": packet.sync_id,
                "format": "jpeg+h264",
            }
        )
        + "\n"
    )
    return thumbnail_written


def _write_motion_state(motion_handle, motion_state) -> None:
    entry = {
        "timestamp": motion_state.timestamp,
        "position": motion_state.position.tolist(),
        "velocity": motion_state.velocity.tolist(),
        "confidence": float(motion_state.confidence),
        "source_id": motion_state.source_id,
        "metadata": motion_state.metadata or {},
        "joints": motion_state.joints.tolist() if motion_state.joints is not None else None,
    }
    motion_handle.write(json.dumps(_json_ready(entry)) + "\n")


def run_workflow(
    video_path: str,
    session_name: str,
    sample_fps: float = 3.0,
    max_frames: Optional[int] = None,
    chunk_frames: int = 100,
) -> Optional[str]:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    source_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_step = max(1, int(round(source_fps / max(sample_fps, 1.0))))
    effective_fps = source_fps / frame_step
    target_resolution = (640, 640)
    session_path = _create_session(session_name)

    print(
        f"[Workflow] Starting offline workflow for {video_path}\n"
        f"[Workflow] Source FPS={source_fps:.3f}, frame_count={source_frame_count}, "
        f"sampling every {frame_step} frame(s) -> effective FPS={effective_fps:.3f}\n"
        f"[Workflow] Session path: {session_path}"
    )

    archive_path = os.path.join(session_path, "session_archive.mp4")
    annotated_path = os.path.join(session_path, "annotated_preview.mp4")
    video_writer = cv2.VideoWriter(
        archive_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        effective_fps,
        target_resolution,
    )
    preview_writer = cv2.VideoWriter(
        annotated_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        effective_fps,
        target_resolution,
    )

    metadata_path = os.path.join(session_path, "metadata.jsonl")
    motion_path = os.path.join(session_path, "motion_states.jsonl")
    metadata_handle = open(metadata_path, "a", encoding="utf-8")
    motion_handle = open(motion_path, "a", encoding="utf-8")

    orchestrator = _new_orchestrator()
    processed_count = 0
    tracked_count = 0
    chunk_count = 0
    thumbnail_written = False
    started = time.time()
    simulation_2d: List[Dict[str, Any]] = []
    simulation_3d: List[Dict[str, Any]] = []
    retarget_frames: List[Dict[str, Any]] = []

    try:
        frame_index = 0
        while True:
            if max_frames is not None and processed_count >= max_frames:
                break

            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % frame_step != 0:
                frame_index += 1
                continue

            if processed_count > 0 and processed_count % chunk_frames == 0:
                chunk_count += 1
                print(f"[Workflow] Recycling perception stack before chunk {chunk_count + 1}...")
                orchestrator.stop_all()
                orchestrator = _new_orchestrator()

            normalized_frame = orchestrator.normalizer.normalize(frame)
            packet = orchestrator.builder.build(
                frame_normalized=normalized_frame,
                frame_full_res=frame,
                source_type=SourceType.VIDEO,
                source_id=os.path.basename(video_path),
                fps=effective_fps,
                index=processed_count,
            )
            packet.timestamp = processed_count / effective_fps if effective_fps else float(processed_count)

            structured_frame = orchestrator.pipeline.process_packet(packet)
            if structured_frame is None:
                frame_index += 1
                continue

            try:
                frame_state = orchestrator.perception.process(structured_frame.frame, packet.timestamp)
            except Exception as exc:
                print(f"[Workflow] Perception failure at frame {processed_count}: {exc}")
                frame_index += 1
                processed_count += 1
                continue

            if frame_state is None:
                print(f"[Workflow] Perception returned no frame state at frame {processed_count}.")
                frame_index += 1
                processed_count += 1
                continue

            annotated = orchestrator.visualizer.draw(packet.frame_normalized, frame_state.subjects)
            preview_writer.write(cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
            thumbnail_written = _write_frame_packet(
                session_path=session_path,
                packet=packet,
                metadata_handle=metadata_handle,
                video_writer=video_writer,
                thumbnail_written=thumbnail_written,
            )

            primary_subject = _select_primary_subject(frame_state.subjects)
            if primary_subject is not None:
                refined_joints, avg_confidence = orchestrator.understanding.process(primary_subject)
                motion_state = orchestrator.fusion.process_refined_joints(
                    primary_subject.subject_id,
                    refined_joints,
                    avg_confidence,
                    packet.source_id,
                    packet.timestamp,
                )
                motion_state.metadata = {
                    "subject_id": primary_subject.subject_id,
                    "bbox": primary_subject.bbox,
                    "tracking": primary_subject.tracking,
                    "pose_2d": _joint_2d_payload(primary_subject),
                }
                _write_motion_state(motion_handle, motion_state)

                human_skeleton = HumanSkeleton(refined_joints)
                robot_joints = orchestrator.joint_mapper.map_to_robot(human_skeleton)

                simulation_2d.append(
                    {
                        "frame_index": processed_count,
                        "timestamp": packet.timestamp,
                        "subject_id": primary_subject.subject_id,
                        "bbox": primary_subject.bbox,
                        "pose": _joint_2d_payload(primary_subject),
                        "tracking": primary_subject.tracking,
                    }
                )
                simulation_3d.append(
                    {
                        "frame_index": processed_count,
                        "timestamp": packet.timestamp,
                        "subject_id": primary_subject.subject_id,
                        "joints": refined_joints.tolist(),
                        "centroid": motion_state.position.tolist(),
                        "velocity": motion_state.velocity.tolist(),
                        "confidence": float(avg_confidence),
                    }
                )
                retarget_frames.append(
                    {
                        "frame_index": processed_count,
                        "timestamp": packet.timestamp,
                        "subject_id": primary_subject.subject_id,
                        "robot_joints": robot_joints,
                    }
                )
                tracked_count += 1

            processed_count += 1
            frame_index += 1

            if processed_count % 50 == 0:
                elapsed = time.time() - started
                print(
                    f"[Workflow] processed={processed_count:5d} | tracked={tracked_count:5d} "
                    f"| elapsed={elapsed:7.1f}s"
                )
    finally:
        cap.release()
        orchestrator.stop_all()
        metadata_handle.close()
        motion_handle.close()
        video_writer.release()
        preview_writer.release()

    exporter = TrainingExporter()
    if not exporter.process_session(session_path):
        raise RuntimeError(f"Training export failed for session: {session_path}")

    npy_path = os.path.join(session_path, "training_set.npy")
    if not os.path.exists(npy_path):
        raise RuntimeError(f"Expected training set missing: {npy_path}")

    payload = np.load(npy_path, allow_pickle=True).item()
    actions = payload.get("actions", np.empty((0, 0)))
    timestamps = payload.get("timestamps", np.array([]))
    if not isinstance(actions, np.ndarray) or actions.size == 0:
        raise RuntimeError("Training export did not produce robot action data.")

    bvh_path = os.path.join(session_path, "blender_export.bvh")
    BVHExporter().export({}, actions.tolist(), bvh_path)

    gltf_tracks = _collect_gltf_tracks(actions, timestamps)
    gltf_json = GLTFExporter().export_to_json(gltf_tracks)
    with open(os.path.join(session_path, "gltf_animation.json"), "w", encoding="utf-8") as handle:
        handle.write(gltf_json)

    _write_json(
        os.path.join(session_path, "simulation_2d.json"),
        {
            "source_video": video_path,
            "sample_fps": effective_fps,
            "frames": simulation_2d,
        },
    )
    _write_json(
        os.path.join(session_path, "simulation_3d.json"),
        {
            "source_video": video_path,
            "sample_fps": effective_fps,
            "frames": simulation_3d,
        },
    )
    _write_json(
        os.path.join(session_path, "retargeted_motion.json"),
        {
            "source_video": video_path,
            "sample_fps": effective_fps,
            "frames": retarget_frames,
        },
    )
    _write_json(
        os.path.join(session_path, "workflow_summary.json"),
        {
            "source_video": video_path,
            "session_path": session_path,
            "source_fps": source_fps,
            "effective_fps": effective_fps,
            "processed_frames": processed_count,
            "tracked_frames": tracked_count,
            "chunk_frames": chunk_frames,
            "artifacts": {
                "annotated_preview": annotated_path,
                "training_set_npy": npy_path,
                "training_set_csv": os.path.join(session_path, "training_set.csv"),
                "simulation_2d": os.path.join(session_path, "simulation_2d.json"),
                "simulation_3d": os.path.join(session_path, "simulation_3d.json"),
                "retargeted_motion": os.path.join(session_path, "retargeted_motion.json"),
                "gltf_animation": os.path.join(session_path, "gltf_animation.json"),
                "blender_export_bvh": bvh_path,
            },
        },
    )

    elapsed = time.time() - started
    print(
        f"[Workflow] Completed. processed_frames={processed_count}, tracked_frames={tracked_count}, "
        f"elapsed={elapsed:.1f}s"
    )
    print(f"[Workflow] Session artifacts available at: {session_path}")
    return session_path


def main():
    parser = argparse.ArgumentParser(description="Run Sign-Verse video workflow end to end.")
    parser.add_argument("--video", required=True, help="Absolute path to the input video.")
    parser.add_argument("--session", default="test1_run", help="Base name for the recording session.")
    parser.add_argument("--sample-fps", type=float, default=3.0, help="Offline processing FPS for the batch run.")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional cap for smoke tests.")
    parser.add_argument("--chunk-frames", type=int, default=100, help="Recycle perception stack after this many sampled frames.")
    args = parser.parse_args()

    session_path = run_workflow(
        video_path=args.video,
        session_name=args.session,
        sample_fps=args.sample_fps,
        max_frames=args.max_frames,
        chunk_frames=args.chunk_frames,
    )
    if session_path:
        print(session_path)


if __name__ == "__main__":
    main()
