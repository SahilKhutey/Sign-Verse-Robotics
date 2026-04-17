import asyncio
import uuid
import threading
import time
import os
from typing import Dict, List, Optional, Any, Callable
from src.ingestion.schemas import SourceType, UnifiedInputPacket, MotionSequence
from src.ingestion.bus import StreamBus
from src.ingestion.builder import PacketBuilder
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.adapters.camera import CameraAdapter
from src.ingestion.adapters.video import VideoAdapter
from src.ingestion.adapters.youtube import YouTubeAdapter
from src.ingestion.pipeline import IngestionPipeline
from src.perception.orchestrator import PerceptionOrchestrator
from src.motion.understanding.engine import MotionUnderstandingEngine
from src.motion.engine import MotionFusionEngine

# Hardening & Monitoring
from src.ingestion.monitoring.latency import LatencyTracker
from src.ingestion.monitoring.drop_detector import FrameDropMonitor
from src.ingestion.monitoring.guard import MemoryGuard
from src.ingestion.monitoring.sync import StreamSyncTester
from src.monitoring.collector import MetricsCollector
from src.monitoring.alerts import AlertEngine

# Storage & Dataset Engine (Phase 5)
from src.storage.recorder import DatasetRecorder
from src.storage.motion_recorder import MotionStateRecorder
from src.storage.indexer import IndexManager
from src.storage.cloud import CloudStorageHook

# Kinematics & Robotics Bridge (Phase 6)
from src.motion.kinematics.models.human import HumanSkeleton
from src.motion.kinematics.models.robot import UniversalHumanoidModel
from src.motion.kinematics.mapping.mapper import JointMapper
from src.motion.kinematics.solvers.ik import SimpleIK
from src.motion.bridge.robot_bridge import RoboticsBridge

# Intelligence Layer (Phase 7 - TIE)
from src.motion.intelligence.pipeline import IntelligencePipeline

class Orchestrator:
    """
    Production Orchestrator for Sign-Verse Robotics.
    Now includes a full Production Dataset Engine for recording and archival.
    """
    def __init__(self):
        # 1. Ingestion Core
        self.bus = StreamBus(maxsize=500)
        self.builder = PacketBuilder()
        self.normalizer = FrameNormalizer(target_size=(640, 640), target_fps=30)
        
        # 2. Ingestion Pipeline (Production Layer)
        self.pipeline = IngestionPipeline()
        
        # 3. ML Engines
        self.perception = PerceptionOrchestrator()
        self.understanding = MotionUnderstandingEngine()
        self.fusion = MotionFusionEngine()
        
        # 3. Hardening & Monitoring
        self.latency_tracker = LatencyTracker()
        self.drop_monitor = FrameDropMonitor()
        self.memory_guard = MemoryGuard(threshold_mb=1500.0)
        self.sync_tester = StreamSyncTester()
        self.metrics = MetricsCollector()
        self.alert_engine = AlertEngine()
        
        # 4. Dataset Engine (Phase 5)
        self.recorder = DatasetRecorder()
        self.motion_recorder = MotionStateRecorder()
        self.cloud_hook = CloudStorageHook(bucket_name=os.getenv("SIGNVERSE_BUCKET"))
        # 5. Kinematics & Robotics Bridge (Phase 6)
        self.robot_model = UniversalHumanoidModel()
        self.joint_mapper = JointMapper(self.robot_model)
        self.ik_solver = SimpleIK()
        # 6. Intelligence Layer (Phase 7 - TIE)
        self.intelligence = IntelligencePipeline(segment_threshold=0.02)
        
        self.active_adapters: Dict[str, Any] = {}
        self.is_running = False
        self.is_recording = False

    def start_recording(self, session_name: str):
        """Activates the full dataset recording suite."""
        self.recorder.start_session(session_name)
        session_path = self.recorder.session_path
        
        self.motion_recorder.start(session_path)
        self.index_manager = IndexManager(session_path)
        self.cloud_hook.start()
        
        self.is_recording = True
        print(f"[Orchestrator] Recording session started: {session_name}")

    def stop_recording(self):
        """Gracefully shuts down recording and indexes metadata."""
        if not self.is_recording:
            return
            
        self.recorder.stop_session()
        self.motion_recorder.stop()
        self.cloud_hook.stop()
        
        # Optional: Queue the entire session directory for cloud sync
        if self.recorder.session_path:
            self.cloud_hook.queue_upload(self.recorder.session_path, f"datasets/{os.path.basename(self.recorder.session_path)}")
            
        self.is_recording = False
        print("[Orchestrator] Recording session finalized.")

    def get_health_report(self) -> Dict[str, Any]:
        snapshot = self.metrics.snapshot()
        is_safe, mem_mb = self.memory_guard.check()
        return {
            "status": "Healthy" if is_safe else "Critical (High Memory)",
            "memory_usage_mb": round(mem_mb, 2),
            "is_recording": self.is_recording,
            "metrics": snapshot,
            "alerts": self.alert_engine.check(snapshot),
            "sync_drift_ms": round(self.sync_tester.compute_drift() * 1000.0, 2)
        }

    def start_ingestion(self, source_type: SourceType, source_uri: str) -> str:
        adapter_id = str(uuid.uuid4())
        if source_type == SourceType.CAMERA:
            adapter = CameraAdapter(self.bus, self.normalizer, self.builder, camera_id=int(source_uri))
        elif source_type == SourceType.VIDEO:
            adapter = VideoAdapter(self.bus, self.normalizer, self.builder, video_path=source_uri)
        elif source_type == SourceType.YOUTUBE:
            adapter = YouTubeAdapter(self.bus, self.normalizer, self.builder, youtube_url=source_uri)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        adapter.start()
        self.active_adapters[adapter_id] = adapter
        return adapter_id

    async def process_loop(self, callback: Optional[Callable] = None):
        self.is_running = True
        print("[Orchestrator] Processing loop active...")
        
        async def pipeline_step(packet: UnifiedInputPacket):
            # 2. Ingestion Pipeline (Standardize & Structure)
            structured_frame = self.pipeline.process_packet(packet)
            if structured_frame is None:
                return

            # 3. Perception (Multi-Modal Multi-Human)
            # We pass the frame to the orchestrator which handles all sub-models
            frame_state = self.perception.process(structured_frame.frame, packet.timestamp)
            self.metrics.update_subject_count(len(frame_state.subjects))
            
            # 4. Motion Understanding & Fusion (Per-Subject)
            human_states = []
            for subject in frame_state.subjects:
                # 4a. Semantic understanding (Fusion + Smoothing + Refinement + Normalization)
                refined_joints, avg_confidence = self.understanding.process(subject)
                
                # 4b. Fusion Engine (Temporal stabilization)
                motion_state = self.fusion.process_refined_joints(
                    subject.subject_id, refined_joints, avg_confidence, packet.source_id, packet.timestamp
                )
                
                # 5. Kinematics & Mapping
                if motion_state.joints is not None:
                    human_skeleton = HumanSkeleton(motion_state.joints)
                    joint_angles = self.joint_mapper.map_to_robot(human_skeleton)
                    self.robot_bridge.dispatch(joint_angles) # Baseline mirroring

                # 6. Intelligence Pipeline (AIE + MAIL V3 - Subject Level)
                h_state = self.intelligence.process(motion_state, subject.subject_id, subject.face)
                human_states.append(h_state)

            # 7. Scene Intelligence (Priority Balancing)
            if human_states:
                prioritized_states = self.intelligence.process_scene(human_states)
                primary_subject = max(prioritized_states, key=lambda s: s.priority)
                self.metrics.record_intent(primary_subject.intent, primary_subject.confidence)
                
                # Update Dashboard/C2 with Priority State
                # self.c2_bridge.broadcast_social_state(primary_subject.serialize())

            # 8. Recording Hook (Phase 5)
            if self.is_recording:
                # Store frame and state
                self.recorder.record_packet(packet)
                self.motion_recorder.record(motion_state)
                # Update SQLite Index
                if self.index_manager:
                    self.index_manager.index_packet(
                        packet.frame_index, packet.timestamp, packet.source_id, packet.sync_id
                    )

            if callback:
                await callback(motion_state, packet.frame_full_res, structured_frame)

        await self.bus.consume(pipeline_step)

    def stop_all(self):
        self.stop_recording()
        for adapter in self.active_adapters.values():
            adapter.stop()
        self.perception.release()

    def update_intelligence_config(self, threshold: float):
        """Updates the TIE segmenter sensitivity."""
        self.intelligence.update_segmentation_threshold(threshold)
