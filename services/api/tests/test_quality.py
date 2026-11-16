from io import BytesIO

from app.core.config import Settings
from app.main import create_app
from app.schemas.quality import QualityResponse
from fastapi.testclient import TestClient
from PIL import Image


def upload(payload: bytes, name: str = "field.png", content_type: str = "image/png"):
    return {"image": (name, BytesIO(payload), content_type)}


def test_quality_accepts_sharp_image_and_matches_schema(client, sharp_png):
    response = client.post("/quality", files=upload(sharp_png))
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    assert result.acceptable is True
    assert result.measurements.width == 800
    assert result.quality_status.value == "accepted"


def test_quality_rejects_blurry_image_with_action(client, blurry_png):
    response = client.post("/quality", files=upload(blurry_png))
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    assert result.acceptable is False
    assert "focus_or_blur" in {reason.code for reason in result.rejection_reasons}
    assert result.actionable_instructions


def test_quality_rejects_underexposed_image(client, dark_png):
    response = client.post("/quality", files=upload(dark_png))
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    assert result.acceptable is False
    assert "underexposure" in {reason.code for reason in result.rejection_reasons}


def test_quality_rejects_overexposed_image(client):
    bright = BytesIO()
    Image.new("RGB", (800, 600), color=(255, 255, 255)).save(bright, format="PNG")
    response = client.post("/quality", files=upload(bright.getvalue()))
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    reason_codes = {reason.code for reason in result.rejection_reasons}
    assert "overexposure" in reason_codes
    assert "clipped_highlights" in reason_codes


def test_quality_rejects_unsupported_format(client):
    gif = BytesIO()
    Image.new("RGB", (16, 16)).save(gif, format="GIF")
    response = client.post(
        "/quality",
        files={"image": ("field.gif", BytesIO(gif.getvalue()), "image/gif")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_quality_rejects_invalid_image_bytes(client):
    response = client.post(
        "/quality",
        files={"image": ("field.png", BytesIO(b"not an image"), "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "image_decode_failed"


def test_quality_enforces_upload_size_limit():
    client = TestClient(create_app(settings=Settings(_env_file=None, max_upload_bytes=16)))
    response = client.post(
        "/quality",
        files={"image": ("field.png", BytesIO(b"x" * 17), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"


def test_quality_rejects_identifying_metadata_field(client, sharp_png):
    response = client.post(
        "/quality",
        files=upload(sharp_png),
        data={"capture_metadata": '{"patient_name":"not-allowed"}'},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_capture_metadata"
