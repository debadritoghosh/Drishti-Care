from PIL import Image
from services.image_service import validate_image

def test_valid_dimensions_pass_basic_check():
    ok, _ = validate_image(Image.new("RGB", (640, 480)))
    assert ok

def test_too_small_image_rejected():
    ok, _ = validate_image(Image.new("RGB", (64, 64)))
    assert not ok
