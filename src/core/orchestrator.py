import asyncio
import uuid
import threading
import time
import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from src.ingestion.schemas import SourceType, UnifiedInputPacket, MotionSequence
from src.ingestion.bus import StreamBus
from src.ingestion.builder import PacketBuilder
from src.ingestion.normalizer import FrameNormalizer
from src.ingestion.adapters.camera import CameraAdapter
from src.ingestion.adapters.video import VideoAdapter
from src.ingestion.adapters.youtube import YouTubeAdapter
from src.ingestion.adapters.image import ImageAdapter
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
from src.perception.visualizer import SkeletonVisualizer

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
# Simulation & External Bridges
from src.bridge.blender_bridge import blender_bridge
from src.bridge.isaac_bridge import isaac_bridge
from src.motion.bridge.robot_bridge import RoboticsBridge

# Intelligence Layer (Phase 7 - TIE)
from src.motion.intelligence.pipeline import IntelligencePipeline
from src.motion.intelligence.tie.trainer import MotionTrainer
from src.motion.intelligence.embedding import MotionEmbedding

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
        self.embedding_engine = MotionEmbedding()
        
        # 3b. Bridges
        self.blender_bridge = blender_bridge
        self.isaac_bridge = isaac_bridge
        
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
        self.robot_bridge = RoboticsBridge()
        
        # 6. Intelligence Layer (Phase 7 - TIE)
        self.intelligence = IntelligencePipeline(segment_threshold=0.02)
        self.trainer = MotionTrainer(
            model=self.intelligence.tie_model,
            metrics_hook=self.metrics.record_training
        )
        
        self.active_adapters: Dict[str, Any] = {}
        self.is_running = False
        self.is_recording = False
        self.is_training = False
        self.demonstration_threshold = 1000 # Autonomous trigger
        self.last_demo_count = 0
        self.show_annotations = True
        self.visualizer = SkeletonVisualizer()
        self.bridge_status = {
            "blender_enabled": True,
            "isaac_enabled": True
        }
        
        # Performance Hardening: Metrics Caching
        self._cached_report: Dict[str, Any] = {}
        self._report_lock = threading.Lock()
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Dynamic GPU Scaling
        self._gpu_type = self._detect_gpu()
        self.max_full_detail_subjects = 2 if "940M" in self._gpu_type else 5
        print(f"[Orchestrator] Hardware Detected: {self._gpu_type}. Subject Cap: {self.max_full_detail_subjects}")

    def _detect_gpu(self) -> str:
        try:
            import subprocess
            res = subprocess.check_output(
                ["Powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name | Out-String"],
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            if "NVIDIA" in res:
                name = [line for line in res.split('\n') if "NVIDIA" in line][0].strip()
                return name
            return "Intel/Generic"
        except:
            return "Unknown"

    def stop_ingestion(self):
        """Stops all currently active ingestion adapters."""
        for adapter_id, adapter in list(self.active_adapters.items()):
            try:
                adapter.stop()
            except Exception as e:
                print(f"[Orchestrator] Warning stopping adapter {adapter_id}: {e}")
            finally:
                self.active_adapters.pop(adapter_id, None)

    def start_recording(
        self,
        session_name: str,
        fps: float = 30.0,
        resolution: tuple = (640, 640),
    ):
        """Activates the full dataset recording suite."""
        self.recorder.start_session(session_name, fps=fps, resolution=resolution)
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
        """Returns the high-speed cached health report for telemetry."""
        with self._report_lock:
            if not self._cached_report:
                return {"status": "Initializing"}
            return self._cached_report

    def _update_health_report_snapshot(self):
        """Internal synchronous snapshot of system health. Now cached."""
        # Update bridge status before snapshot
        self.metrics.bridge_status["blender"] = len(self.blender_bridge.active_connections) > 0
        self.metrics.bridge_status["isaac"] = True 
        
        snapshot = self.metrics.snapshot()
        is_safe, mem_mb = self.memory_guard.check()
        
        # Consolidate telemetry
        snapshot["global"]["fps"] = self.metrics.compute_fps("global")
        
        report = {
            "status": "Healthy" if is_safe else "Critical (High Memory)",
            "memory_usage_mb": round(mem_mb, 2),
            "is_recording": self.is_recording,
            "metrics": snapshot,
            "active_adapters": [aid for aid, a in self.active_adapters.items() if getattr(a, 'running', False)],
            "alerts": self.alert_engine.check(snapshot),
            "sync_drift_ms": round(self.sync_tester.compute_drift() * 1000.0, 2),
            "gpu_info": {
                "name": self._gpu_type,
                "detail_cap": self.max_full_detail_subjects
            }
        }
        with self._report_lock:
            self._cached_report = report

    async def _background_metrics_updater(self):
        """Drives the metrics sampling at 10Hz to avoid blocking WebSocket calls."""
        while self.is_running:
            try:
                # Offload the heavy health report logic to a thread to keep event loop responsive
                await asyncio.to_thread(self._update_health_report_snapshot)
            except Exception as e:
                print(f"[Orchestrator] Metrics updater error: {e}")
            await asyncio.sleep(0.1) # 10Hz refresh is plenty for dashboard v2

    def start_ingestion(self, source_type: SourceType, source_uri: str) -> str:
        self.stop_ingestion()
        adapter_id = str(uuid.uuid4())
        if source_type == SourceType.CAMERA:
            adapter = CameraAdapter(self.bus, self.normalizer, self.builder, camera_id=int(source_uri))
        elif source_type == SourceType.VIDEO:
            adapter = VideoAdapter(self.bus, self.normalizer, self.builder, video_path=source_uri)
        elif source_type == SourceType.YOUTUBE:
            adapter = YouTubeAdapter(self.bus, self.normalizer, self.builder, source_uri)
        elif source_type == SourceType.IMAGE:
            adapter = ImageAdapter(self.bus, self.normalizer, self.builder, source_uri)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        adapter.start()
        self.active_adapters[adapter_id] = adapter
        return adapter_id

    async def process_loop(self, callback: Optional[Callable] = None):
        self.is_running = True
        print("[Orchestrator] Processing loop active...")
        
        # Start background metrics updater
        self._metrics_task = asyncio.create_task(self._background_metrics_updater())

        # Limited perception task queue to prevent temporal drift/lag
        task_queue = asyncio.Queue(maxsize=3)
        
        async def perception_worker():
            while self.is_running:
                packet, structured_frame = await task_queue.get()
                try:
                    primary_motion_state = None
                    subject_motion_states = {}
                    subject_joint_angles = {}
                    # 3. Perception (Multi-Modal Multi-Human) - Offloaded to THREAD
                    start_percept = time.time()
                    
                    # Dynamic Detail Gating & Fallback (Production Optimization)
                    health = self.get_health_report()
                    self.perception.detail_cap = self.max_full_detail_subjects
                    
                    # Thermal Fallback Logic (User Request 2)
                    if health.get("status") == "Critical (High Memory)":
                        self.perception.detail_cap = 1 
                        self.perception.detection_interval = 60
                    
                    # Offload perception to worker
                    frame_state = await asyncio.to_thread(self.perception.process, structured_frame.frame, packet.timestamp)
                    
                    self.metrics.record_frame(packet.source_id)
                    self.metrics.record_latency(packet.source_id, time.time() - packet.timestamp)
                    self.metrics.update_subject_count(len(frame_state.subjects))
                    
                    if len(frame_state.subjects) > 0:
                        # Log heartbeat at 1Hz instead of every frame to reduce terminal noise
                        if self.perception.frame_count % 30 == 0:
                            print(f"[Orchestrator] Perception Stable: {len(frame_state.subjects)} subject(s) @ {1.0/(time.time()-start_percept):.1f}Hz (Det: Every {self.perception.detection_interval}f)")
                    
                    # 4. Motion Understanding & Fusion (Per-Subject)
                    human_states = []
                    for subject in frame_state.subjects:
                        decision_start = time.time()
                        
                        # 4a. Semantic understanding
                        refined_joints, avg_confidence = self.understanding.process(subject)
                        
                        # 4b. Fusion Engine
                        motion_state = self.fusion.process_refined_joints(
                            subject.subject_id, refined_joints, avg_confidence, packet.source_id, packet.timestamp
                        )
                        motion_state.metadata = {
                            "subject_id": subject.subject_id,
                            "bbox": subject.bbox,
                            "tracking": subject.tracking,
                        }
                        subject_motion_states[subject.subject_id] = motion_state
                        
                        # 5. Kinematics & Mapping
                        if motion_state.joints is not None:
                            # 5a. Hand Intelligence (Latent Space Viewer Support)
                            if subject.right_hand:
                                hand_lms = np.array([[lm.x, lm.y, lm.z] for lm in subject.right_hand.skeleton])
                                hand_vec = self.embedding_engine.encode_hand(hand_lms)
                                self.metrics.hand_embedding = hand_vec.tolist()
                                self.metrics.hand_joints = hand_lms.tolist()
                            elif subject.left_hand:
                                hand_lms = np.array([[lm.x, lm.y, lm.z] for lm in subject.left_hand.skeleton])
                                hand_vec = self.embedding_engine.encode_hand(hand_lms)
                                self.metrics.hand_embedding = hand_vec.tolist()
                                self.metrics.hand_joints = hand_lms.tolist()

                            # 5b. Robotic Mapping
                            human_skeleton = HumanSkeleton(motion_state.joints)
                            joint_angles = self.joint_mapper.map_to_robot(human_skeleton)
                            subject_joint_angles[subject.subject_id] = joint_angles
                            
                            control_start = time.time()
                            self.robot_bridge.dispatch(joint_angles) # Baseline mirroring
                            
                            # 5c. Simulator Broadcasts
                            if self.bridge_status.get("blender_enabled", True):
                                asyncio.create_task(self.blender_bridge.broadcast(joint_angles)) # Async WebSocket
                                
                            if self.bridge_status.get("isaac_enabled", True):
                                self.isaac_bridge.broadcast(joint_angles) # Sync UDP
                            
                            # Simulate Stability, Velocity & Power Drain for Dashboard telemetry
                            stability = 1.0 - (0.05 * np.random.random())
                            velocity = [0.1 * np.random.randn(), 0.05 * np.random.randn(), 0.0]
                            power_drain = 120.0 + (30.0 * np.random.random())
                            
                            self.metrics.record_stability(stability)
                            self.metrics.record_robot_state(velocity, power_drain)
                            self.metrics.record_control_latency((time.time() - control_start) * 1000.0)

                        # 6. Intelligence Pipeline (AIE + MAIL V3 - Subject Level)
                        h_state = self.intelligence.process(motion_state, subject.subject_id, subject.face)
                        human_states.append(h_state)
                        
                        # 6a. Autonomous Training Check
                        current_demos = len(self.intelligence.dataset_logger.demos)
                        self.metrics.update_dataset_stats(current_demos)
                        
                        if not self.is_training and (current_demos - self.last_demo_count) >= self.demonstration_threshold:
                           asyncio.create_task(self.trigger_training())
                           self.last_demo_count = current_demos
                        
                        self.metrics.record_rl_latency((time.time() - decision_start) * 1000.0)

                    # 7. Scene Intelligence (Priority Balancing)
                    if human_states:
                        prioritized_states = self.intelligence.process_scene(human_states)
                        primary_subject = max(prioritized_states, key=lambda s: s.priority)
                        self.metrics.record_intent(primary_subject.intent, primary_subject.confidence)
                        primary_motion_state = subject_motion_states.get(primary_subject.subject_id)
                        primary_subject.robot_payload = subject_joint_angles.get(primary_subject.subject_id, {})

                    # 8. Recording Hook (Phase 5)
                    if self.is_recording and primary_motion_state is not None:
                        self.recorder.record_packet(packet)
                        self.motion_recorder.record(primary_motion_state)
                        if self.index_manager:
                            self.index_manager.index_packet(
                                packet.frame_index, packet.timestamp, packet.source_id, packet.sync_id
                            )

                    # 9. Dashboard Streaming Hook (Only draw if enabled)
                    try:
                        if self.show_annotations:
                            self.latest_annotated_frame = self.visualizer.draw(packet.frame_normalized, frame_state.subjects)
                        else:
                            self.latest_annotated_frame = packet.frame_normalized
                            
                    except Exception as e:
                        print(f"[Orchestrator] Error annotating stream: {e}")

                    if callback and primary_motion_state is not None:
                        await callback(primary_motion_state, packet.frame_full_res, structured_frame)
                
                except Exception as e:
                    print(f"[Orchestrator Error] Perception loop failed: {e}")
                finally:
                    task_queue.task_done()
                    
        # Start 1 worker to handle perception (Prevents multi-threading contention on lower-end CPUs)
        workers = [asyncio.create_task(perception_worker())]

        async def pipeline_step(packet: UnifiedInputPacket):
            await asyncio.sleep(0.001)
            # 2. Ingestion Pipeline (Standardize & Structure)
            structured_frame = self.pipeline.process_packet(packet)
            if structured_frame is None:
                return
            
            # Enqueue to perception worker non-blocking
            if not task_queue.full():
                task_queue.put_nowait((packet, structured_frame))
            else:
                self.metrics.record_drops(packet.source_id, 1)

        try:
            await self.bus.consume(pipeline_step)
        finally:
            self.is_running = False
            for w in workers:
                w.cancel()

    def toggle_recording(self):
        """Toggles the global recording state."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording(f"session_{int(time.time())}")
        return self.is_recording

    def emergency_stop(self):
        """High-priority lockdown of all systems."""
        print("[CRITICAL] EMERGENCY STOP ACTIVATED")
        try:
            self.stop_all()
        except Exception as e:
            print(f"[RECOVERY] Cleanup warning: {e}")
        self.is_running = False
        return {"status": "EMERGENCY_STOP_COMPLETE"}

    async def trigger_training(self, epochs: int = 10):
        """Launches an asynchronous active learning sweep."""
        if self.is_training:
            return
        
        self.is_training = True
        print(f"[Orchestrator] Starting Active Learning sweep ({epochs} epochs)...")
        try:
            demos = self.intelligence.dataset_logger.demos
            if not demos:
                print("[Orchestrator] Training Aborted: No demonstration data available.")
                return
            await self.trainer.train_active(demos, epochs=epochs)
        except Exception as e:
            print(f"[Orchestrator] Training Error: {e}")
        finally:
            self.is_training = False

    async def calibrate(self):
        """Resets solvers, state machines, and notifies simulators."""
        print("[Orchestrator] Initializing Global System Calibration...")
        
        # 1. Reset Internal Solvers
        self.intelligence.calibrate()
        self.joint_mapper.reset()
        self.metrics.training_metrics["accuracy"] = 0.0 # Reset session stats
        
        # 2. Reset External Simulators
        await self.blender_bridge.reset()
        self.isaac_bridge.reset()
        
        print("[Orchestrator] System Calibrated & Synthesized.")
        return {"status": "SUCCESS", "message": "Global System Calibrated"}

    def stop_all(self):
        self.stop_recording()
        self.stop_ingestion()
        self.perception.release()

    def update_intelligence_config(self, threshold: float):
        """Updates the TIE segmenter sensitivity."""
        self.intelligence.update_segmentation_threshold(threshold)
