import json
import time
from typing import Dict, Any, List

class SkillExtractor:
    """
    Analyzes robotic motion sequences to extract behavioral primitives.
    Differentiates between 'energetic', 'calm', and 'precise' interactions.
    """
    def categorize(self, motion_sequence: List[Dict[str, Any]]) -> str:
        if len(motion_sequence) < 10:
            return "incomplete"
            
        # Calculate max velocity over sequence
        vels = []
        for i in range(1, len(motion_sequence)):
            v = np.linalg.norm(np.array(motion_sequence[i]["pos"]) - np.array(motion_sequence[i-1]["pos"]))
            vels.append(v)
            
        max_v = max(vels)
        if max_v > 0.4: return "energetic_social"
        if max_v < 0.05: return "static_attention"
        return "natural_engagement"

class DemonstrationBuilder:
    """
    Records high-fidelity HRI demonstrations for imitation learning.
    Stores [HumanState -> RobotAction -> Reward] triplets.
    """
    def __init__(self, output_path: str = "storage/datasets/sim_demo_v1.json"):
        self.output_path = output_path
        self.demos = []

    def record(self, state: Dict[str, Any], action: Dict[str, Any], reward: float):
        entry = {
            "timestamp": time.time(),
            "state": state,
            "action": action,
            "reward": reward
        }
        self.demos.append(entry)
        
        # Periodic autosave
        if len(self.demos) % 100 == 0:
            self.save()

    def save(self):
        with open(self.output_path, "w") as f:
            json.dump(self.demos, f, indent=4)
        print(f"📦 Dataset Saved: {len(self.demos)} demonstrations.")
