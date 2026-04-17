import numpy as np
from typing import Dict, List, Optional

class EmbeddingStore:
    """
    Stores motion and facial embeddings for long-term subject recognition and style analysis.
    """
    def __init__(self, max_embeddings_per_user: int = 100):
        self.max_per_user = max_embeddings_per_user
        # subject_id -> List[np.ndarray]
        self.store: Dict[int, List[np.ndarray]] = {}

    def add(self, user_id: int, embedding: np.ndarray):
        """
        Adds a new behavioral embedding to the user's history.
        """
        if user_id not in self.store:
            self.store[user_id] = []
            
        history = self.store[user_id]
        history.append(embedding)
        
        if len(history) > self.max_per_user:
            history.pop(0)

    def get_average_embedding(self, user_id: int) -> Optional[np.ndarray]:
        """
        Computes the 'signature' embedding for a user.
        """
        if user_id not in self.store or not self.store[user_id]:
            return None
        return np.mean(self.store[user_id], axis=0)
