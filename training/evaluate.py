import argparse
from pathlib import Path
import pandas as pd
import torch
from torch.utils.data import DataLoader
from torchvision import models, transforms
from torch import nn
from sklearn.metrics import classification_report, confusion_matrix, cohen_kappa_score
from PIL import Image
import json

class EvalDataset(torch.utils.data.Dataset):
    def __init__(self, frame, image_dir, size=224):
        self.frame = frame.reset_index(drop=True); self.image_dir = Path(image_dir)
        self.tf = transforms.Compose([transforms.Resize((size,size)), transforms.ToTensor(),
            transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    def __len__(self): return len(self.frame)
    def __getitem__(self, i):
        row = self.frame.iloc[i]
        return self.tf(Image.open(self.image_dir / f"{row.id_code}.png").convert("RGB")), int(row.diagnosis)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir", required=True); p.add_argument("--model-path", required=True)
    p.add_argument("--batch-size", type=int, default=16); p.add_argument("--image-size", type=int, default=224)
    args=p.parse_args(); root=Path(args.data_dir)
    df=pd.read_csv(root/"train.csv")
    # Warning: this is a quick demonstration evaluation on all labelled images and is NOT an independent test.
    ds=EvalDataset(df, root/"train_images", args.image_size)
    loader=DataLoader(ds,batch_size=args.batch_size,shuffle=False,num_workers=0)
    model=models.efficientnet_b0(weights=None); model.classifier[1]=nn.Linear(model.classifier[1].in_features,5)
    model.load_state_dict(torch.load(args.model_path,map_location="cpu",weights_only=True)); model.eval()
    y_true=[]; y_pred=[]
    with torch.inference_mode():
        for x,y in loader:
            pred=model(x).argmax(1)
            y_true.extend(y.tolist()); y_pred.extend(pred.tolist())
    print("WARNING: This is not a valid held-out test if training used these images.")
    print(classification_report(y_true,y_pred,zero_division=0))
    print("Confusion matrix:\n",confusion_matrix(y_true,y_pred))
    print("Quadratic weighted kappa:", cohen_kappa_score(y_true,y_pred,weights="quadratic"))

if __name__=="__main__": main()
