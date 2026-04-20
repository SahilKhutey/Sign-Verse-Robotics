import argparse
import json
import os
import re
import sys
import time
from hashlib import sha1
from typing import Any, Dict, List

import cv2

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.render_check import verify_session
from scripts.run_video_workflow import run_workflow


VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def _slugify(name: str) -> str:
    stem = os.path.splitext(name)[0].lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return stem[:48] or "video"


def _inspect_video(path: str) -> Dict[str, Any]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_s = (frame_count / fps) if fps else 0.0
    cap.release()

    name = os.path.basename(path)
    lower_name = name.lower()
    likely_youtube = any(token in lower_name for token in ["ted", "tedx", "gopro", "pov"])

    return {
        "name": name,
        "path": path,
        "fps": fps,
        "frame_count": frame_count,
        "duration_s": duration_s,
        "width": width,
        "height": height,
        "source_kind": "local_file",
        "likely_youtube_video": likely_youtube,
    }


def _choose_sample_fps(duration_s: float) -> float:
    if duration_s >= 1200:
        return 2.0
    if duration_s >= 900:
        return 2.25
    if duration_s >= 600:
        return 2.5
    return 3.0


def _collect_videos(folder: str) -> List[str]:
    files: List[str] = []
    for entry in sorted(os.listdir(folder)):
        path = os.path.join(folder, entry)
        if os.path.isfile(path) and os.path.splitext(entry)[1].lower() in VIDEO_EXTENSIONS:
            files.append(path)
    return files


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_batch(folder: str, chunk_frames: int = 90, sample_fps_override: float | None = None) -> str:
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Video folder not found: {folder}")

    batch_id = time.strftime("svbatch_%Y%m%d_%H%M%S")
    batch_dir = os.path.join(PROJECT_ROOT, "datasets", "batches", batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    videos = _collect_videos(folder)
    if not videos:
        raise RuntimeError(f"No supported video files found in: {folder}")

    batch_manifest: Dict[str, Any] = {
        "batch_id": batch_id,
        "video_folder": folder,
        "created_at_epoch": time.time(),
        "video_count": len(videos),
        "videos": [],
    }

    for index, video_path in enumerate(videos, start=1):
        inspection = _inspect_video(video_path)
        sample_fps = sample_fps_override if sample_fps_override is not None else _choose_sample_fps(inspection["duration_s"])
        source_hash = sha1(video_path.encode("utf-8")).hexdigest()[:8]
        session_base = f"{batch_id}_{index:02d}_{_slugify(inspection['name'])}_{source_hash}"

        print(
            f"[Batch] ({index}/{len(videos)}) {inspection['name']}\n"
            f"[Batch] duration={inspection['duration_s']:.1f}s fps={inspection['fps']:.3f} "
            f"frames={inspection['frame_count']} sample_fps={sample_fps:.2f}"
        )

        started = time.time()
        session_path = run_workflow(
            video_path=video_path,
            session_name=session_base,
            sample_fps=sample_fps,
            chunk_frames=chunk_frames,
        )
        if not session_path:
            raise RuntimeError(f"Workflow did not return a session path for {video_path}")

        session_name = os.path.basename(session_path)
        verification_ok = verify_session(session_name)
        workflow_summary_path = os.path.join(PROJECT_ROOT, session_path, "workflow_summary.json")
        workflow_summary = {}
        if os.path.exists(workflow_summary_path):
            with open(workflow_summary_path, "r", encoding="utf-8") as handle:
                workflow_summary = json.load(handle)

        per_video_manifest = {
            "session_name": session_name,
            "session_path": session_path,
            "inspection": inspection,
            "workflow": {
                "sample_fps": sample_fps,
                "chunk_frames": chunk_frames,
                "elapsed_s": time.time() - started,
                "verification_ok": verification_ok,
            },
            "summary": workflow_summary,
        }

        _write_json(os.path.join(PROJECT_ROOT, session_path, "source_manifest.json"), per_video_manifest)
        _write_json(os.path.join(batch_dir, f"{index:02d}_{_slugify(inspection['name'])}.json"), per_video_manifest)
        batch_manifest["videos"].append(per_video_manifest)
        _write_json(os.path.join(batch_dir, "batch_manifest.json"), batch_manifest)

    return batch_dir


def main():
    parser = argparse.ArgumentParser(description="Run the Sign-Verse batch workflow on a folder of videos.")
    parser.add_argument("--folder", required=True, help="Absolute path to the folder of videos.")
    parser.add_argument("--chunk-frames", type=int, default=90, help="Recycle the perception stack after this many sampled frames.")
    args = parser.parse_args()

    batch_dir = run_batch(args.folder, chunk_frames=args.chunk_frames)
    print(batch_dir)


if __name__ == "__main__":
    main()
