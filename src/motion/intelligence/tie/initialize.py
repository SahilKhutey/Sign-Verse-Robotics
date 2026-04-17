import torch
import os
from src.motion.intelligence.tie.model import IntentTransformer
from src.motion.intelligence.tie.trainer import MotionTrainer

def initialize_tie_v2():
    """
    Initializes a fresh TIE v2 model and saves mock weights for pipeline integration.
    """
    print("🚀 Initializing TIE v2 (Transformer Intent Engine)...")
    
    # 1. Instantiate Model
    model = IntentTransformer(
        input_dim=256, 
        d_model=256, 
        n_heads=8, 
        n_layers=4, 
        n_classes=7
    )
    
    # 2. Setup Trainer
    trainer = MotionTrainer(model)
    
    # 3. Save Mock Weights
    checkpoint_path = "models/tie_v2/checkpoints/latest.pt"
    trainer.save_model(checkpoint_path)
    
    print(f"✅ TIE v2 initialized with baseline weights at: {checkpoint_path}")

if __name__ == "__main__":
    initialize_tie_v2()
