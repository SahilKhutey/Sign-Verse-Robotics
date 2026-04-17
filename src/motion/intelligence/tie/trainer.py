import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from src.motion.intelligence.tie.model import IntentTransformer
from src.motion.intelligence.tie.dataset import MotionDataset
import os
from typing import Dict, Any

class MotionTrainer:
    """
    Standard Training loop for TIE v2 models.
    Supports checkpointing and progress tracking.
    """
    def __init__(self, model: nn.Module, lr: float = 1e-4):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=lr)
        self.criterion = nn.CrossEntropyLoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def train_epoch(self, dataloader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        
        for batch_x, batch_y in dataloader:
            batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
            
            # Forward
            logits = self.model(batch_x)
            loss = self.criterion(logits, batch_y)
            
            # Backward
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
        return total_loss / len(dataloader)

    def save_model(self, path: str = "models/tie_v2/checkpoints/latest.pt"):
        """Saves current model weights for inference testing."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        self.model.load_state_dict(torch.load(path))
        print(f"Model loaded from {path}")
