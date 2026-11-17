from io import BytesIO
from pathlib import Path

import numpy as np
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


def test_quality_rejects_image_below_field_minimum_dimensions(client):
    small = BytesIO()
    rng = np.random.default_rng(13)
    pixels = rng.integers(20, 235, size=(240, 320, 3), dtype=np.uint8)
    Image.fromarray(pixels, mode="RGB").save(small, format="PNG")
    response = client.post("/quality", files=upload(small.getvalue()))
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    assert result.acceptable is False
    assert "minimum_dimensions" in {reason.code for reason in result.rejection_reasons}


def test_quality_rejects_decoded_image_over_pixel_limit(sharp_png):
    limited = TestClient(
        create_app(settings=Settings(_env_file=None, max_image_pixels=100_000))
    )
    response = limited.post("/quality", files=upload(sharp_png))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "image_dimensions_too_large"


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


def test_quality_rejects_declared_format_mismatch(client, sharp_png):
    response = client.post(
        "/quality",
        files={"image": ("field.jpg", BytesIO(sharp_png), "image/jpeg")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "file_format_mismatch"


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


def test_quality_accepts_non_identifying_capture_profile_id(client, sharp_png):
    response = client.post(
        "/quality",
        files=upload(sharp_png),
        data={"capture_metadata": '{"capture_profile_id":"phone-a_microscope-1"}'},
    )
    assert response.status_code == 200


def test_quality_endpoint_decodes_bundled_public_sample(client):
    project_root = Path(__file__).resolve().parents[3]
    sample = (
        project_root
        / "apps/mobile/assets/samples/white_blood_cell_on_blood_smear_unstained.jpg"
    )
    response = client.post(
        "/quality",
        files={
            "image": (
                sample.name,
                BytesIO(sample.read_bytes()),
                "image/jpeg",
            )
        },
    )
    assert response.status_code == 200
    result = QualityResponse.model_validate(response.json())
    assert result.measurements.width == 715
    assert result.measurements.height == 615
