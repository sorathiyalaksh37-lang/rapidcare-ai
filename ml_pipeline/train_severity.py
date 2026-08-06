"""
Task 9 — Severity & Survival Predictor Training (Phase 2)
==========================================================
Trains a PyTorch Feed-Forward Neural Network to predict
patient survival probability based on 50 contextual features.
Exports to ONNX.
"""
import os
import argparse
from pathlib import Path

def train_severity_model(epochs=50, batch_size=32):
    print("🚀 Initializing Severity/Survival Training Pipeline...")
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import TensorDataset, DataLoader
    except ImportError:
        print("❌ Error: Missing ML dependencies (torch).")
        print("Run: pip install torch onnx")
        return

    # 1. Define Model Architecture
    class SurvivalPredictor(nn.Module):
        def __init__(self, input_dim=50):
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 1),
                nn.Sigmoid() # Output probability 0-1
            )
            
        def forward(self, x):
            return self.network(x)

    model = SurvivalPredictor(input_dim=50)

    # 2. Mock Dataset (50 features)
    print("📊 Generating synthetic training data...")
    # 1000 samples, 50 features
    X_train = torch.rand(1000, 50)
    y_train = torch.rand(1000, 1) # Target survival probabilities
    
    dataset = TensorDataset(X_train, y_train)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # 3. Training Setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 4. Train Loop
    print(f"🔥 Starting training for {epochs} epochs...")
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs} - Loss: {epoch_loss/len(dataloader):.4f}")

    # 5. Export to ONNX (Task 10)
    print("📦 Exporting to ONNX format...")
    onnx_dir = Path("models/onnx_severity")
    onnx_dir.mkdir(parents=True, exist_ok=True)
    
    onnx_path = onnx_dir / "survival_predictor.onnx"
    dummy_input = torch.randn(1, 50)
    
    torch.onnx.export(
        model, 
        dummy_input, 
        str(onnx_path),
        input_names=["input"],
        output_names=["survival_prob"],
        dynamic_axes={"input": {0: "batch_size"}, "survival_prob": {0: "batch_size"}},
        opset_version=14
    )
    
    print(f"✅ Severity Model exported successfully to {onnx_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()
    
    train_severity_model(epochs=args.epochs, batch_size=args.batch_size)
