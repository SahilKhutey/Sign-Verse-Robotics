import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from src.motion.intelligence.tie.model import IntentTransformer
from src.motion.intelligence.tie.dataset import MotionDataset
import os
import time
from typing import Dict, Any, Optional, Callable

class MotionTrainer:
    """
    Standard Training loop for TIE v2 models.
    Supports checkpointing and progress tracking with real-time telemetry.
    """
    def __init__(self, model: nn.Module, lr: float = 1e-4, metrics_hook: Optional[Callable] = None):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=lr)
        self.criterion = nn.CrossEntropyLoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.metrics_hook = metrics_hook

    def train_epoch(self, epoch: int, dataloader: DataLoader) -> Dict[str, float]:
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
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
            
            # Accuracy
            _, predicted = torch.max(logits.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
            
        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total
        
        # Report to dashboard via hook
        if self.metrics_hook:
            self.metrics_hook(epoch, avg_loss, accuracy)
            
        return {"loss": avg_loss, "accuracy": accuracy}

    async def train_active(self, raw_data: list, epochs: int = 10):
        """
        Executes an Active Learning sweep on demonstration data.
        Asynchronous to prevent blocking the perception pipeline.
        """
        if not raw_data:
            return
            
        # 1. Prepare Dataset
        dataset = MotionDataset(raw_data)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        print(f"[MotionTrainer] Launching Active Learning sweep on {len(raw_data)} samples...")
        
        for epoch in range(1, epochs + 1):
            stats = self.train_epoch(epoch, dataloader)
            print(f"Epoch {epoch}/{epochs} | Loss: {stats['loss']:.4f} | Acc: {stats['accuracy']:.4f}")
            # Simulate a small sleep to avoid total CPU pegging during live sessions
            await torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
        self.save_model()
        if self.metrics_hook:
            self.metrics_hook(epochs, stats['loss'], stats['accuracy'], is_training=False)

    def save_model(self, path: str = "models/tie_v2/checkpoints/latest.pt"):
        """Saves current model weights for inference testing."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        self.model.load_state_dict(torch.load(path))
        print(f"Model loaded from {path}")
