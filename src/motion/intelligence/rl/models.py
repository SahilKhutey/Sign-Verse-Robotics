import torch
import torch.nn as nn
from typing import Tuple

class ActorNetwork(nn.Module):
    """
    Policy Network (Actor) for HRI discrete social actions.
    Input: 6D State Representation
    Output: Softmax Probabilities across 6 Action Classes
    """
    def __init__(self, state_dim: int = 6, action_dim: int = 6):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.LayerNorm(128),
            nn.Tanh(), # Tanh often works better for social/bounded stability
            nn.Linear(128, 128),
            nn.Tanh(),
            nn.Linear(128, action_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Output probability distribution
        return torch.softmax(self.net(x), dim=-1)

class CriticNetwork(nn.Module):
    """
    Value Network (Critic) for HRI State Evaluation.
    Output: Single scalar representing state value V(s).
    """
    def __init__(self, state_dim: int = 6):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.LayerNorm(128),
            nn.Tanh(),
            nn.Linear(128, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
