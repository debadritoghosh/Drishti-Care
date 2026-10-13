import io
from PIL import Image, UnidentifiedImageError
from config.settings import UPLOAD_MAX_MB

ALLOWED_FORMATS = {"JPEG", "PNG"}

def read_uploaded_image(uploaded_file):
    data = uploaded_file.getvalue()
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > UPLOAD_MAX_MB * 1024 * 1024:
        raise ValueError(f"File exceeds the {UPLOAD_MAX_MB} MB upload limit.")
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("File is not a valid supported image.") from exc
    return data, image

def validate_image(image):
    if image.width < 128 or image.height < 128:
        return False, "Image dimensions are too small for this workflow."
    if image.width > 8000 or image.height > 8000:
        return False, "Image dimensions exceed the supported limit."
    if image.width * image.height > 32_000_000:
        return False, "Image has too many pixels."
    return True, "Basic file checks passed; retinal gradability is not established."
