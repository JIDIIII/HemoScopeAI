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
    assert adapter.calls == 0


def test_missing_model_returns_clear_error(client, sharp_png):
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "true"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


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
    assert "SIMULATED" in payload["warning"]


def test_crop_confirmation_validation_has_consistent_error(client, sharp_png):
    response = client.post(
        "/analyze",
        files=crop_upload(sharp_png),
        data={"crop_confirmed": "false"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "crop_confirmation_required"
