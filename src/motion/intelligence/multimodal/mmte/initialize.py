import torch
import os
from src.motion.intelligence.multimodal.mmte.model import MultiModalTransformer

def initialize_mmte():
    """
    TIE v3: Initializing the Multimodal Transformer Engine (MMTE).
    Generates baseline weights for the unified 345D architecture.
    """
    print("Initializing MMTE (Multimodal Transformer Engine)...")
    
    # 1. Instantiate Model (345D -> 6-Layers -> 3 Heads)
    model = MultiModalTransformer(
        input_dim=345,
        d_model=256,
        n_heads=8,
        n_layers=6
    )
    
    # 2. Setup Persistence Path
    checkpoint_path = "models/mmte/checkpoints/latest.pt"
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    
    # 3. Save Baseline Weights
    torch.save(model.state_dict(), checkpoint_path)
    
    print(f"MMTE initialized with baseline weights at: {checkpoint_path}")
    print(f"Context Window: 90 frames (3.0s)")

if __name__ == "__main__":
    initialize_mmte()
