from io import BytesIO

from app.core.config import Settings
from app.main import create_app
from app.schemas.analysis import AnalysisStatus, InferenceMode
from app.services.inference import InferenceResult


class SpyInferenceAdapter:
    model_available = True
    model_version = "test-adapter"
    inference_mode = "real"

    def __init__(self):
        self.calls = 0

    async def predict(self, image_bytes: bytes, research_session_id):
        del image_bytes, research_session_id
        self.calls += 1
        return InferenceResult(
            analysis_status=AnalysisStatus.REVIEW_REQUIRED,
            model_label="test_only",
            raw_model_score=0.5,
            model_version=self.model_version,
            inference_mode=InferenceMode.REAL,
            warning="Test adapter output.",
            all_score=0.8,
            decision_policy_version="test-policy-v1",
        )


def crop_upload(payload: bytes):
    return {"cell_crop": ("cell.png", BytesIO(payload), "image/png")}


def test_rejected_crop_never_reaches_classifier(settings, blurry_png):
    from fastapi.testclient import TestClient

    adapter = SpyInferenceAdapter()
    client = TestClient(create_app(settings=settings, inference_adapter=adapter))
    response = client.post(
        "/analyze",
        files=crop_upload(blurry_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 200
    assert response.json()["analysis_status"] == "recapture_required"
    assert response.json()["quality_status"] == "rejected"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["rejection_reasons"]
    assert response.json()["actionable_instructions"]
    assert adapter.calls == 0


def test_missing_model_returns_explicit_inconclusive_response(client, sharp_png):
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_status"] == "inconclusive"
    assert payload["quality_status"] == "accepted"
    assert payload["inference_mode"] == "unavailable"
    assert payload["model_label"] is None
    assert payload["raw_model_score"] is None
    assert payload["model_version"] is None
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert "no classification was performed" in payload["warning"].lower()


def test_extracted_mobile_crop_needs_neither_source_bounds_nor_session_id(client, sharp_png):
    from PIL import Image

    crop = BytesIO()
    with Image.open(BytesIO(sharp_png)) as field:
        field.crop((0, 0, 128, 128)).save(crop, format="PNG")
    response = client.post(
        "/analyze",
        files=crop_upload(crop.getvalue()),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["quality_status"] == "accepted"
    assert payload["analysis_status"] == "inconclusive"
    assert payload["inference_mode"] == "unavailable"
    assert payload["research_session_id"] is None
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_cloud_provider_stub_fails_closed_without_fabricating_output(sharp_png):
    from fastapi.testclient import TestClient

    configured = Settings(
        _env_file=None,
        inference_provider="ecs",
        huawei_ecs_inference_url="https://inference.example.invalid/predict",
    )
    client = TestClient(create_app(settings=configured))
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 503
    payload = response.json()["error"]
    assert payload["code"] == "model_unavailable"
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_demo_mock_is_explicitly_simulated(settings, sharp_png):
    from fastapi.testclient import TestClient

    simulated_settings = Settings(_env_file=None, enable_demo_mock=True)
    client = TestClient(create_app(settings=simulated_settings))
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_status"] == "inconclusive"
    assert payload["inference_mode"] == "simulated"
    assert payload["raw_model_score"] is None
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert "SIMULATED" in payload["warning"]


def test_crop_confirmation_validation_has_consistent_error(client, sharp_png):
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "false"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "crop_confirmation_required"


def test_field_crop_bounds_extract_before_quality_and_classification(settings, sharp_png):
    from fastapi.testclient import TestClient

    adapter = SpyInferenceAdapter()
    client = TestClient(create_app(settings=settings, inference_adapter=adapter))
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={
            "crop_confirmed": "true",
            "crop_bounds": '{"x":0.1,"y":0.1,"width":0.6,"height":0.6}',
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_status"] == "review_required"
    assert payload["quality_status"] == "accepted"
    assert payload["model_version"] == "test-adapter"
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert adapter.calls == 1


def test_too_small_field_crop_is_rejected_before_classifier(settings, sharp_png):
    from fastapi.testclient import TestClient

    adapter = SpyInferenceAdapter()
    client = TestClient(create_app(settings=settings, inference_adapter=adapter))
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={
            "crop_confirmed": "true",
            "crop_bounds": '{"x":0.1,"y":0.1,"width":0.05,"height":0.05}',
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_status"] == "recapture_required"
    assert payload["quality_status"] == "rejected"
    assert "minimum_dimensions" in {reason["code"] for reason in payload["rejection_reasons"]}
    assert payload["actionable_instructions"]
    assert adapter.calls == 0


def test_invalid_crop_bounds_return_structured_error(client, sharp_png):
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={
            "crop_confirmed": "true",
            "crop_bounds": '{"x":0.9,"y":0.1,"width":0.2,"height":0.5}',
        },
    )
    assert response.status_code == 422
    payload = response.json()["error"]
    assert payload["code"] == "invalid_crop_bounds"
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_real_inference_without_model_version_is_rejected(settings, sharp_png):
    from fastapi.testclient import TestClient

    class MissingVersionAdapter(SpyInferenceAdapter):
        async def predict(self, image_bytes: bytes, research_session_id):
            del image_bytes, research_session_id
            return InferenceResult(
                analysis_status=AnalysisStatus.REVIEW_REQUIRED,
                model_label="test_only",
                raw_model_score=0.5,
                model_version=None,
                inference_mode=InferenceMode.REAL,
                warning="Test adapter output.",
            )

    client = TestClient(create_app(settings=settings, inference_adapter=MissingVersionAdapter()))
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 502
    payload = response.json()["error"]
    assert payload["code"] == "inference_response_invalid"
    assert payload["request_id"] == response.headers["X-Request-ID"]
