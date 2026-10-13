from PIL import Image
from ai.inference import predict_image, model_available

def test_missing_model_does_not_fabricate_prediction(monkeypatch, tmp_path):
    import ai.inference as inf
    monkeypatch.setattr(inf, "model_available", lambda: False)
    result = inf.predict_image(Image.new("RGB", (224, 224)))
    assert result["status"] == "model_not_configured"
    assert result["grade"] is None
