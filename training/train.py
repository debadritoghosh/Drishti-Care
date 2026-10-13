import argparse, json, random
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import models, transforms
from PIL import Image
from sklearn.model_selection import train_test_split

class AptosDataset(Dataset):
    def __init__(self, frame, image_dir, transform):
        self.frame = frame.reset_index(drop=True)
        self.image_dir = Path(image_dir)
        self.transform = transform
    def __len__(self):
        return len(self.frame)
    def __getitem__(self, index):
        row = self.frame.iloc[index]
        path = self.image_dir / f"{row['id_code']}.png"
        image = Image.open(path).convert("RGB")
        return self.transform(image), int(row["diagnosis"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", required=True)
    p.add_argument("--output-dir", default="ai/artifacts")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--image-size", type=int, default=224)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    root = Path(args.data_dir)
    frame = pd.read_csv(root / "train.csv")
    required = {"id_code", "diagnosis"}
    if not required.issubset(frame.columns):
        raise ValueError("train.csv must contain id_code and diagnosis columns.")
    frame["diagnosis"] = frame["diagnosis"].astype(int)
    frame = frame[frame["diagnosis"].between(0, 4)]
    missing = [x for x in frame["id_code"] if not (root / "train_images" / f"{x}.png").exists()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} image files missing; first missing id: {missing[0]}")
    train_df, val_df = train_test_split(frame, test_size=0.2, random_state=args.seed, stratify=frame["diagnosis"])
    train_transform = transforms.Compose([
        transforms.Resize((args.image_size, args.image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.05),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])
    eval_transform = transforms.Compose([
        transforms.Resize((args.image_size, args.image_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])
    train_ds = AptosDataset(train_df, root / "train_images", train_transform)
    val_ds = AptosDataset(val_df, root / "train_images", eval_transform)
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU is not available. This project is configured to train ONLY on your NVIDIA GPU. "
            "Install the CUDA-enabled PyTorch build and verify torch.cuda.is_available() before training."
        )
    device = torch.device("cuda:0")
    print("Training device:", torch.cuda.get_device_name(0))
    torch.backends.cudnn.benchmark = True
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 5)
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    scaler = torch.amp.GradScaler("cuda")
    best_loss = float("inf")
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    for epoch in range(args.epochs):
        model.train(); running_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                logits = model(x)
                loss = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            running_loss += loss.item() * x.size(0)
        model.eval(); val_loss = 0.0; correct = 0; total = 0
        with torch.inference_mode():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    logits = model(x)
                    loss = criterion(logits, y)
                val_loss += loss.item() * x.size(0)
                correct += (logits.argmax(1) == y).sum().item(); total += y.size(0)
        val_loss /= max(total, 1)
        print(f"Epoch {epoch+1}/{args.epochs}: train_loss={running_loss/len(train_ds):.4f} val_loss={val_loss:.4f} val_accuracy={correct/max(total,1):.4f}")
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.cpu().state_dict(), output / "efficientnet_b0.pth")
            model.to(device)
    metadata = {
        "model_version": "aptos-efficientnet-b0-baseline-v0.1",
        "architecture": "torchvision.models.efficientnet_b0",
        "image_size": args.image_size,
        "class_labels": ["No DR", "Mild", "Moderate", "Severe", "Proliferative"],
        "dataset": "APTOS 2019 Blindness Detection",
        "clinical_validation": False,
        "warning": "Research baseline only; not for clinical use.",
    }
    (output / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved model to {output.resolve()}")

if __name__ == "__main__":
    main()
