import torch
import torch.nn as nn
from collections import deque
from typing import Tuple, Optional, List
import numpy as np
from src.motion.intelligence.tie.labels import IntentLabels

class IntentInferenceEngine:
    """
    Real-Time Transformer-based Intent Inference Engine (TIE v2).
    Maintains a sliding window of representations and executes model forward pass.
    """
    def __init__(self, model: nn.Module, seq_len: int = 60):
        self.model = model
        self.model.eval()
        self.seq_len = seq_len
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Per-subject sliding window
        self.buffers: Dict[int, deque] = {}

    def update(self, subject_id: int, representation: np.ndarray) -> Tuple[str, float]:
        """
        Updates the temporal buffer for a subject and returns the inferred intent.
        """
        if subject_id not in self.buffers:
            self.buffers[subject_id] = deque(maxlen=self.seq_len)
            
        buffer = self.buffers[subject_id]
        buffer.append(representation)
        
        # We need a full window for high-confidence sequence decoding
        if len(buffer) < self.seq_len:
            return "IDLE", 0.0
            
        # Convert Buffer to Tensor (Batch=1, SeqLen, Dim)
        input_tensor = torch.tensor([list(buffer)], dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=-1)
            
        # Extract Result
        top_prob, top_idx = torch.max(probs, dim=-1)
        intent_idx = int(top_idx.item())
        confidence = float(top_prob.item())
        
        intent_name = IntentLabels.get_name(intent_idx)
        return intent_name, confidence

    def clear(self, subject_id: int):
        if subject_id in self.buffers:
            del self.buffers[subject_id]
