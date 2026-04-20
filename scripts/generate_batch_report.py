import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _load_manifest(batch_dir: str) -> Dict[str, Any]:
    manifest_path = os.path.join(batch_dir, "batch_manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Batch manifest not found: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_rows(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in videos:
        inspection = item.get("inspection", {})
        workflow = item.get("workflow", {})
        summary = item.get("summary", {})
        processed = int(summary.get("processed_frames", 0))
        tracked = int(summary.get("tracked_frames", 0))
        row = {
            "video_name": inspection.get("name"),
            "session_name": item.get("session_name"),
            "source_path": inspection.get("path"),
            "duration_s": round(float(inspection.get("duration_s", 0.0)), 3),
            "source_fps": round(float(inspection.get("fps", 0.0)), 3),
            "sample_fps": round(float(workflow.get("sample_fps", 0.0)), 3),
            "processed_frames": processed,
            "tracked_frames": tracked,
            "track_ratio": round((tracked / processed) if processed else 0.0, 4),
            "verification_ok": bool(workflow.get("verification_ok")),
            "elapsed_s": round(float(workflow.get("elapsed_s", 0.0)), 3),
            "likely_youtube_video": bool(inspection.get("likely_youtube_video")),
        }
        rows.append(row)
    return rows


def generate_report(batch_dir: str) -> Dict[str, str]:
    manifest = _load_manifest(batch_dir)
    rows = _build_rows(manifest.get("videos", []))

    processed_total = sum(row["processed_frames"] for row in rows)
    tracked_total = sum(row["tracked_frames"] for row in rows)
    verified_total = sum(1 for row in rows if row["verification_ok"])

    report_json = {
        "batch_id": manifest.get("batch_id"),
        "video_folder": manifest.get("video_folder"),
        "video_count": manifest.get("video_count", len(rows)),
        "completed_count": len(rows),
        "verified_count": verified_total,
        "processed_frames_total": processed_total,
        "tracked_frames_total": tracked_total,
        "overall_track_ratio": round((tracked_total / processed_total) if processed_total else 0.0, 4),
        "videos": rows,
    }

    csv_path = os.path.join(batch_dir, "consolidated_report.csv")
    json_path = os.path.join(batch_dir, "consolidated_report.json")

    if rows:
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            handle.write("")

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report_json, handle, indent=2)

    return {"csv_path": csv_path, "json_path": json_path}


def main():
    parser = argparse.ArgumentParser(description="Generate a consolidated batch report from a Sign-Verse batch manifest.")
    parser.add_argument("--batch-dir", required=True, help="Absolute path to the batch directory.")
    args = parser.parse_args()

    paths = generate_report(args.batch_dir)
    print(json.dumps(paths, indent=2))


if __name__ == "__main__":
    main()
