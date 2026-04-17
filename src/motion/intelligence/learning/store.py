import json
import os
from typing import Dict, Optional
from src.motion.intelligence.learning.profile import UserProfile

class ProfileStore:
    """
    Persistent storage for UserProfiles.
    Designed for shared access in multi-robot environments.
    """
    def __init__(self, storage_path: str = "data/profiles/"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self._cache: Dict[int, UserProfile] = {}

    def get(self, subject_id: int) -> UserProfile:
        """Retrieves profile from cache or disk."""
        if subject_id in self._cache:
            return self._cache[subject_id]
            
        file_path = os.path.join(self.storage_path, f"{subject_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                profile = UserProfile.deserialize(data)
                self._cache[subject_id] = profile
                return profile
        
        # New profile
        new_profile = UserProfile(subject_id=subject_id)
        self._cache[subject_id] = new_profile
        return new_profile

    def save(self, profile: UserProfile):
        """Persists profile to disk."""
        self._cache[profile.subject_id] = profile
        file_path = os.path.join(self.storage_path, f"{profile.subject_id}.json")
        with open(file_path, 'w') as f:
            json.dump(profile.serialize(), f, indent=4)

    def reset_profile(self, subject_id: int):
        """Clears a specific subject's learned intelligence."""
        if subject_id in self._cache:
            del self._cache[subject_id]
        
        file_path = os.path.join(self.storage_path, f"{subject_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

    def reset_all(self):
        """Wipes the entire cognitive memory of the system."""
        self._cache.clear()
        for filename in os.listdir(self.storage_path):
            file_path = os.path.join(self.storage_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
