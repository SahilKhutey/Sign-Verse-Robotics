import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]

class MultiModalTransformer(nn.Module):
    """
    MMTE: Unified Multimodal Transformer Engine.
    Fuses Motion, Face, Engagement, Context, and Spatial features.
    Predicts Intent, Emotion, and Engagement level simultaneously.
    """
    def __init__(self, 
                 input_dim: int = 345, 
                 d_model: int = 256, 
                 n_heads: int = 8, 
                 n_layers: int = 6):
        super().__init__()
        
        # 1. Input Projection
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        # 2. Hybrid Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # 3. Multi-Head Output
        self.pool = nn.AdaptiveAvgPool1d(1)
        
        # Head A: Intent (12 Classes)
        self.intent_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, 12)
        )
        
        # Head B: Emotion (5 Classes: Happy, Neutral, Sad, Angry, Surprise)
        self.emotion_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 5)
        )
        
        # Head C: Engagement (Regression 0-1)
        self.engagement_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> (torch.Tensor, torch.Tensor, torch.Tensor):
        # x: (Batch, Seq_Len, 345)
        
        x = self.input_proj(x)
        x = self.pos_encoder(x)
        x = self.transformer(x)
        
        # Global temporal pooling
        x = x.transpose(1, 2) # (B, D, T)
        x = self.pool(x).squeeze(-1) # (B, D)
        
        intent = self.intent_head(x)
        emotion = self.emotion_head(x)
        engagement = self.engagement_head(x).squeeze(-1)
        
        return intent, emotion, engagement
