from typing import List, Dict, Any

class EngagementBalancer:
    """
    Normalizes subject engagement across the current perception set.
    Determines 'Relative Priority' for robotic attention focus.
    """
    def balance(self, subjects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Computes priority scores normalized by total scene activity.
        """
        if not subjects:
            return []
            
        # 1. Calculate Total Scene Engagement
        total_engagement = sum(s.get("engagement", 0.0) for s in subjects) + 1e-6
        
        # 2. Assign Relative Priority
        balanced_subjects = []
        for s in subjects:
            priority = s.get("engagement", 0.0) / total_engagement
            s["priority"] = priority
            balanced_subjects.append(s)
            
        return balanced_subjects
