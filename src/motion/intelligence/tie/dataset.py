import torch
from torch.utils.data import Dataset
import numpy as np
from typing import List, Tuple

class MotionDataset(Dataset):
    """
    Sequence-aligned Motion Dataset for TIE v2 training.
    Loads sequences of high-density representations as (X, Y) pairs.
    """
    def __init__(self, sequences: np.ndarray, labels: np.ndarray):
        """
        Args:
            sequences: Array of shape (NumSamples, SeqLen, FeatureDim)
            labels: Array of shape (NumSamples,)
        """
        self.X = torch.from_numpy(sequences).float()
        self.y = torch.from_numpy(labels).long()

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]

class SequenceProcessor:
    """
    Utility for translating raw interaction logs into windowed training samples.
    """
    def segment_logs(self, log_data: List[np.ndarray], seq_len: int = 60, stride: int = 5) -> np.ndarray:
        """
        Converts a continuous stream of representations into overlapping sequences.
        """
        sequences = []
        for i in range(0, len(log_data) - seq_len, stride):
            sequences.append(log_data[i : i + seq_len])
        return np.array(sequences)
