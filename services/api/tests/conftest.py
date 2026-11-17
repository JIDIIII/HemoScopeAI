from io import BytesIO

import numpy as np
import pytest
from app.core.config import Settings
from app.main import create_app
from app.services.inference import InferenceResult
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter


class SpyInferenceAdapter:
    model_available = True
    model_version = "test-adapter"
    inference_mode = "real"

    def __init__(self) -> None:
        self.calls = 0

    async def predict(self, image_bytes: bytes, research_session_id):
        del image_bytes, research_session_id
        self.calls += 1
        from app.schemas.analysis import AnalysisStatus, InferenceMode

        return InferenceResult(
            analysis_status=AnalysisStatus.REVIEW_REQUIRED,
            model_label="test_only",
            raw_model_score=0.5,
            model_version=self.model_version,
            inference_mode=InferenceMode.REAL,
            warning="Test adapter output.",
        )


def image_bytes(image: Image.Image, format_name: str = "PNG") -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=format_name)
    return buffer.getvalue()


@pytest.fixture
def sharp_png() -> bytes:
    rng = np.random.default_rng(7)
    pixels = rng.integers(20, 235, size=(600, 800, 3), dtype=np.uint8)
    return image_bytes(Image.fromarray(pixels, mode="RGB"))


@pytest.fixture
def blurry_png() -> bytes:
    rng = np.random.default_rng(9)
    pixels = rng.integers(20, 235, size=(600, 800, 3), dtype=np.uint8)
    blurred = Image.fromarray(pixels, mode="RGB").filter(ImageFilter.GaussianBlur(radius=18))
    return image_bytes(blurred)


@pytest.fixture
def dark_png() -> bytes:
    return image_bytes(Image.new("RGB", (800, 600), color=(0, 0, 0)))


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings=settings))
