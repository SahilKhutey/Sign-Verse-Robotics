import json
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from src.ingestion.adapters.youtube import YouTubeAdapter


DEFAULT_CATEGORIES = ["workout", "dance", "sports", "arts", "cooking"]
AUTO_JOB_ROOT = os.path.join("datasets", "auto_jobs")


class AutoYouTubePipelineJob:
    def __init__(
        self,
        job_id: str,
        categories: List[str],
        results_per_category: int = 1,
        sample_fps: Optional[float] = None,
        chunk_frames: int = 90,
    ):
        self.job_id = job_id
        self.categories = categories
        self.results_per_category = results_per_category
        self.sample_fps = sample_fps
        self.chunk_frames = chunk_frames
        self.status = "pending"
        self.phase = "queued"
        self.message = "Waiting to start."
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.error: Optional[str] = None
        self.downloaded_videos: List[Dict[str, Any]] = []
        self.batch_dir: Optional[str] = None
        self.batch_id: Optional[str] = None
        self.report_paths: Dict[str, str] = {}
        self.thread: Optional[threading.Thread] = None

        self.job_root = os.path.join("datasets", "auto_jobs", self.job_id)
        self.download_dir = os.path.join(self.job_root, "downloads")
        self.manifest_path = os.path.join(self.job_root, "job_manifest.json")
        os.makedirs(self.download_dir, exist_ok=True)

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> "AutoYouTubePipelineJob":
        job = cls(
            job_id=snapshot["job_id"],
            categories=snapshot.get("categories") or list(DEFAULT_CATEGORIES),
            results_per_category=int(snapshot.get("results_per_category", 1) or 1),
            sample_fps=snapshot.get("sample_fps"),
            chunk_frames=int(snapshot.get("chunk_frames", 90) or 90),
        )
        job.status = snapshot.get("status", "pending")
        job.phase = snapshot.get("phase", "queued")
        job.message = snapshot.get("message", "Waiting to start.")
        job.started_at = snapshot.get("started_at")
        job.finished_at = snapshot.get("finished_at")
        job.error = snapshot.get("error")
        job.downloaded_videos = list(snapshot.get("downloaded_videos") or [])
        job.batch_dir = snapshot.get("batch_dir")
        job.batch_id = snapshot.get("batch_id")
        job.report_paths = dict(snapshot.get("report_paths") or {})
        return job

    def snapshot(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "phase": self.phase,
            "message": self.message,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "categories": self.categories,
            "results_per_category": self.results_per_category,
            "sample_fps": self.sample_fps,
            "chunk_frames": self.chunk_frames,
            "download_dir": self.download_dir,
            "downloaded_videos": self.downloaded_videos,
            "batch_dir": self.batch_dir,
            "batch_id": self.batch_id,
            "report_paths": self.report_paths,
        }

    def persist(self) -> None:
        os.makedirs(self.job_root, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as handle:
            json.dump(self.snapshot(), handle, indent=2)


class AutoYouTubePipelineManager:
    def __init__(self):
        self.jobs: Dict[str, AutoYouTubePipelineJob] = {}
        self.latest_job_id: Optional[str] = None
        self._lock = threading.Lock()
        self._restore_jobs()

    def _restore_jobs(self) -> None:
        if not os.path.isdir(AUTO_JOB_ROOT):
            return

        restored_jobs: List[AutoYouTubePipelineJob] = []
        for entry in os.listdir(AUTO_JOB_ROOT):
            manifest_path = os.path.join(AUTO_JOB_ROOT, entry, "job_manifest.json")
            if not os.path.exists(manifest_path):
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    snapshot = json.load(handle)
                job = AutoYouTubePipelineJob.from_snapshot(snapshot)
                if job.status == "running":
                    job.status = "interrupted"
                    job.phase = "interrupted"
                    job.message = "Job was interrupted by a backend restart."
                    job.finished_at = job.finished_at or time.time()
                    job.persist()
                restored_jobs.append(job)
            except Exception:
                continue

        restored_jobs.sort(
            key=lambda job: (
                job.started_at or 0.0,
                job.job_id,
            ),
            reverse=True,
        )
        for job in restored_jobs:
            self.jobs[job.job_id] = job
        if restored_jobs:
            self.latest_job_id = restored_jobs[0].job_id

    def list_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = sorted(
                self.jobs.values(),
                key=lambda job: (job.started_at or 0.0, job.job_id),
                reverse=True,
            )
        return [job.snapshot() for job in jobs[: max(1, limit)]]

    def has_running_job(self) -> bool:
        with self._lock:
            return any(job.status == "running" for job in self.jobs.values())

    def start_job(
        self,
        categories: Optional[List[str]] = None,
        results_per_category: int = 1,
        sample_fps: Optional[float] = None,
        chunk_frames: int = 90,
    ) -> Dict[str, Any]:
        categories = [category.strip() for category in (categories or DEFAULT_CATEGORIES) if category.strip()]
        if not categories:
            categories = list(DEFAULT_CATEGORIES)

        if self.has_running_job():
            raise RuntimeError("An auto YouTube pipeline job is already running.")

        job_id = f"{time.strftime('autoyt_%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        job = AutoYouTubePipelineJob(
            job_id=job_id,
            categories=categories,
            results_per_category=max(1, results_per_category),
            sample_fps=sample_fps,
            chunk_frames=chunk_frames,
        )

        with self._lock:
            self.jobs[job_id] = job
            self.latest_job_id = job_id

        job.thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        job.thread.start()
        job.persist()
        return job.snapshot()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self.jobs.get(job_id)
        return job.snapshot() if job else None

    def get_latest_job(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self.latest_job_id is None:
                return None
            job = self.jobs.get(self.latest_job_id)
        return job.snapshot() if job else None

    def _run_job(self, job: AutoYouTubePipelineJob) -> None:
        try:
            job.status = "running"
            job.phase = "searching"
            job.started_at = time.time()
            job.message = "Searching YouTube categories."
            job.persist()

            downloaded_urls = set()
            for index, category in enumerate(job.categories, start=1):
                query = f"{category} performance tutorial movement"
                results = YouTubeAdapter.search(query, max_results=job.results_per_category)
                if not results:
                    job.message = f"No results found for {category}; continuing."
                    job.persist()
                for result_index, result in enumerate(results, start=1):
                    url = result.get("url")
                    if not url or url in downloaded_urls:
                        continue
                    downloaded_urls.add(url)
                    job.phase = "downloading"
                    job.message = f"Downloading {category} video {result_index}/{len(results)}."
                    job.persist()
                    download = YouTubeAdapter.download_video(
                        url,
                        job.download_dir,
                        filename_prefix=f"{index:02d}_{category.lower()}",
                    )
                    download["category"] = category
                    job.downloaded_videos.append(download)
                    job.persist()

            if not job.downloaded_videos:
                raise RuntimeError("No videos were downloaded from the requested categories.")

            job.phase = "processing"
            job.message = "Running Sign-Verse batch workflow on downloaded videos."
            job.persist()

            from scripts.run_video_batch import run_batch
            from scripts.generate_batch_report import generate_report

            batch_dir = run_batch(job.download_dir, chunk_frames=job.chunk_frames, sample_fps_override=job.sample_fps)
            report_paths = generate_report(batch_dir)

            job.batch_dir = batch_dir
            job.batch_id = os.path.basename(batch_dir)
            job.report_paths = report_paths
            job.phase = "completed"
            job.status = "completed"
            job.message = "Download, processing, and reporting completed."
            job.finished_at = time.time()
            job.persist()
        except Exception as exc:
            job.status = "error"
            job.phase = "failed"
            job.error = str(exc)
            job.message = f"Pipeline failed: {exc}"
            job.finished_at = time.time()
            job.persist()
