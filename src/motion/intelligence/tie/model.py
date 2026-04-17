import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    """
    Injects temporal position information into the motion sequences.
    Ensures the Transformer understands the 'arrow of time' in a gesture.
    """
    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (Batch, SeqLen, Dim)
        return x + self.pe[:, :x.size(1)]

class IntentTransformer(nn.Module):
    """
    TIE v2: Transformer-based Intent Engine for Sequence-Aware Motion Intelligence.
    Learns temporal patterns of gestures from high-density representations.
    """
    def __init__(self, input_dim: int = 256, d_model: int = 256, n_heads: int = 8, n_layers: int = 4, n_classes: int = 7):
        super().__init__()
        
        # 1. Feature Projection
        self.embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        # 2. Transformer Encoder Stack
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 2,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # 3. Decision Head
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, n_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (Batch, Seq_Len, Feature_Dim)
        
        x = self.embedding(x) # (B, T, D)
        x = self.pos_encoder(x)
        
        x = self.transformer(x) # (B, T, D)
        
        # Global Average Pooling over time dimension
        x = x.transpose(1, 2) # (B, D, T)
        x = self.pool(x).squeeze(-1) # (B, D)
        
        logits = self.classifier(x) # (B, Classes)
        return logits
