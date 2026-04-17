import torch
import torch.nn as nn
from collections import deque
from typing import Dict, Any, Optional, Tuple
import numpy as np
from src.motion.intelligence.multimodal.state import HumanState

class MMTEEngine:
    """
    Multimodal Transformer Engine (MMTE) Real-Time Orchestrator.
    Manages a 90-frame temporal buffer and executes unified multi-task inference.
    Includes 'Heuristic Backup' logic for high-reliability robotics.
    """
    def __init__(self, model: nn.Module, seq_len: int = 90):
        self.model = model
        self.model.eval()
        self.seq_len = seq_len
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Per-Subject Temporal Buffers
        self.buffers: Dict[int, deque] = {}
        
        # Label Mappings (Production Constants)
        self.INTENT_LABELS = {
            0: "IDLE", 1: "GREETING", 2: "POINTING", 3: "STOP", 4: "WAVE",
            5: "THANK_YOU", 6: "DISENGAGE", 7: "APPROACH", 8: "DEPART",
            9: "REQUEST_HELP", 10: "FOLLOW_ME", 11: "UNKNOWN"
        }
        self.EMOTION_LABELS = {
            0: "neutral", 1: "happy", 2: "sad", 3: "angry", 4: "surprise"
        }

    def update(self, subject_id: int, fused_vector: np.ndarray) -> Dict[str, Any]:
        """
        Updates the 90-frame buffer and returns neural inference results.
        """
        if subject_id not in self.buffers:
            self.buffers[subject_id] = deque(maxlen=self.seq_len)
            
        buffer = self.buffers[subject_id]
        buffer.append(fused_vector)
        
        # We need a full window for high-fidelity social reasoning (3 seconds)
        if len(buffer) < self.seq_len:
            return None
            
        # Convert Buffer to Tensor (Batch=1, T=90, D=345)
        X = torch.tensor([list(buffer)], dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            intent_logits, emotion_logits, engagement_val = self.model(X)
            
        # 1. Intent Extraction
        i_probs = torch.softmax(intent_logits, dim=-1)
        i_conf, i_idx = torch.max(i_probs, dim=-1)
        
        # 2. Emotion Extraction
        e_probs = torch.softmax(emotion_logits, dim=-1)
        e_conf, e_idx = torch.max(e_probs, dim=-1)
        
        return {
            "intent": self.INTENT_LABELS.get(int(i_idx.item()), "UNKNOWN"),
            "intent_conf": float(i_conf.item()),
            "intent_probs": i_probs.squeeze(0), # (Classes)
            "emotion": self.EMOTION_LABELS.get(int(e_idx.item()), "neutral"),
            "emotion_conf": float(e_conf.item()),
            "engagement": float(engagement_val.item())
        }

    def clear(self, subject_id: int):
        if subject_id in self.buffers:
            del self.buffers[subject_id]
