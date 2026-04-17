from typing import Dict, Any, List
from src.export.retargeting.skeleton_mapper import SkeletonMapper
from src.export.unreal.exporter import UnrealExporter
from src.export.streaming.broadcaster import StreamExporter, RobotPolicyExporter

class RELEngine:
    """
    Unified Render & Export Layer (REL) Orchestrator.
    Bridges internal intelligence with external visualization and hardware.
    """
    def __init__(self, target_rig: str = "mixamo"):
        self.mapper = SkeletonMapper(target_rig=target_rig)
        self.ue5_exporter = UnrealExporter()
        self.broadcaster = StreamExporter()
        self.robot_policy = RobotPolicyExporter()

    def process_frame(self, joint_state: Dict[str, Any], meta: Dict[str, Any]):
        """
        Retargets, formats, and broadcasts a single frame of intelligence.
        """
        # 1. Retarget to target rig
        mapped = self.mapper.retarget(joint_state)
        
        # 2. Format for Unreal (LH Z-up)
        ue5_payload = self.ue5_exporter.to_json_payload(mapped)
        
        # 3. Format for Robot Policy
        robot_cmd = self.robot_policy.export_command(mapped, meta)
        
        # 4. Multicast Broadcast
        self.broadcaster.broadcast({
            "unreal_data": ue5_payload,
            "robot_command": robot_cmd,
            "metadata": meta
        })
        
    def shutdown(self):
        self.broadcaster.close()
