"""
Task 7 — NLP Classifier Training Pipeline (Phase 2)
====================================================
Fine-tunes DistilBERT for Emergency Text Classification and
exports to ONNX format for rapid inference in the backend.

Features:
- HuggingFace Trainer API
- Exports to `models/onnx_distilbert/`
"""
import os
import argparse
from pathlib import Path

def train_nlp_model(epochs=3, batch_size=16):
    print("🚀 Initializing NLP Training Pipeline (DistilBERT)...")
    
    # 1. Imports
    try:
        import torch
        from transformers import (
            AutoTokenizer, 
            AutoModelForSequenceClassification, 
            Trainer, 
            TrainingArguments
        )
        from datasets import Dataset
    except ImportError:
        print("❌ Error: Missing ML dependencies (torch, transformers, datasets).")
        print("Run: pip install torch transformers datasets onnx onnxruntime")
        return

    # 2. Mock dataset for demonstration
    # In production, this would be replaced with the actual labeled dataset (DATASETS.md)
    print("📊 Loading dataset...")
    data = {
        "text": [
            "Car crash on highway, two injured",
            "My father is clutching his chest and collapsed",
            "He cannot speak and his face is drooping",
            "Large fire in apartment building",
            "Fell from roof, bone is sticking out",
            "Bleeding heavily from arm cut",
            "Drowning victim pulled from pool",
            "Hit his head, unconscious",
        ],
        "label": [0, 1, 2, 3, 4, 5, 6, 7] # Corresponds to emergency types
    }
    dataset = Dataset.from_dict(data)

    # 3. Load Tokenizer & Model
    print("🤖 Loading base model: distilbert-base-uncased")
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=8)

    def tokenize_func(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    tokenized_dataset = dataset.map(tokenize_func, batched=True)

    # 4. Training setup
    output_dir = Path("models/checkpoints/nlp")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        logging_steps=10,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    # 5. Train
    print("🔥 Starting training...")
    trainer.train()

    # 6. Export to ONNX (Task 10)
    print("📦 Exporting to ONNX format...")
    onnx_dir = Path("models/onnx_distilbert")
    onnx_dir.mkdir(parents=True, exist_ok=True)
    
    # Save tokenizer
    tokenizer.save_pretrained(str(onnx_dir))

    # Export model
    dummy_input = tokenizer("Test emergency", return_tensors="pt")
    onnx_path = onnx_dir / "model.onnx"
    
    torch.onnx.export(
        model, 
        (dummy_input["input_ids"], dummy_input["attention_mask"]), 
        str(onnx_path),
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size"}
        },
        opset_version=14
    )
    
    print(f"✅ NLP Model exported successfully to {onnx_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    args = parser.parse_args()
    
    train_nlp_model(epochs=args.epochs, batch_size=args.batch_size)
