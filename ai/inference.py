from pathlib import Path
import json
import torch
from PIL import Image
from torchvision import models, transforms

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
WEIGHTS = ARTIFACT_DIR / "efficientnet_b0.pth"
METADATA = ARTIFACT_DIR / "model_metadata.json"
GRADE_LABELS = [
    "Grade 0 — No DR in dataset label",
    "Grade 1 — Mild DR",
    "Grade 2 — Moderate DR",
    "Grade 3 — Severe DR",
    "Grade 4 — Proliferative DR",
]

def model_available():
    return WEIGHTS.exists() and METADATA.exists()

def _load_model():
    if not model_available():
        return None, None
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 5)
    state = torch.load(WEIGHTS, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    transform = transforms.Compose([
        transforms.Resize((int(metadata.get("image_size", 224)), int(metadata.get("image_size", 224)))),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return model, (transform, metadata)

def predict_image(image: Image.Image):
    if not model_available():
        return {
            "status": "model_not_configured",
            "grade": None,
            "grade_label": None,
            "message": "No trained model artifact installed; no prediction was made.",
            "model_version": None,
        }
    model, extras = _load_model()
    transform, metadata = extras
    tensor = transform(image.convert("RGB")).unsqueeze(0)
    with torch.inference_mode():
        logits = model(tensor)
        scores = torch.softmax(logits, dim=1)[0].tolist()
    grade = int(max(range(len(scores)), key=lambda i: scores[i]))
    return {
        "status": "completed",
        "grade": grade,
        "grade_label": GRADE_LABELS[grade],
        "class_scores": scores,
        "model_version": metadata.get("model_version", "unversioned-research-model"),
        "message": "Research-only model output; not a diagnosis or validated referral decision.",
    }
