from typing import Dict, Any
from src.motion.intelligence.learning.profile import UserProfile

class PolicyAdapter:
    """
    Acts as a social filter between decision logic and robotic execution.
    Modulates robotic actions based on subject-specific learned preferences.
    """
    def adapt(self, base_action: Dict[str, Any], profile: UserProfile) -> Dict[str, Any]:
        """
        Refines a base action (command, intensity, speed) using personal weights.
        """
        adapted = base_action.copy()
        
        # 1. Apply Learned Intensity
        intensity_weight = profile.preferred_intensity
        adapted["intensity"] = float(adapted.get("intensity", 1.0) * intensity_weight)
        
        # 2. Dynamic Speed Scaling based on Historical Engagement
        # If user is habitually low-engagement, the robot becomes calmer and slower
        if profile.avg_engagement < 0.3:
            adapted["speed"] = float(adapted.get("speed", 1.0) * 0.8)
            
        # If user is highly engaged, robot becomes more energetic
        elif profile.avg_engagement > 0.7:
            adapted["speed"] = float(adapted.get("speed", 1.0) * 1.2)
            
        # 3. Apply CLIP/Safety limits
        adapted["intensity"] = max(0.2, min(2.5, adapted["intensity"]))
        adapted["speed"] = max(0.2, min(2.5, adapted["speed"]))
        
        return adapted
