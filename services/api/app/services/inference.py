from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.config import Settings
from app.schemas.analysis import AnalysisStatus, InferenceMode


class ModelUnavailableError(Exception):
    """No real or explicitly enabled development inference adapter is available."""


@dataclass(frozen=True)
class InferenceResult:
    analysis_status: AnalysisStatus
    model_label: str | None
    raw_model_score: float | None
    model_version: str | None
    inference_mode: InferenceMode
    warning: str


class InferenceAdapter(Protocol):
    model_available: bool
    model_version: str | None
    inference_mode: str

    async def predict(
        self, image_bytes: bytes, research_session_id: UUID | None
    ) -> InferenceResult: ...


class UnavailableInferenceAdapter:
    model_available = False
    model_version = None
    inference_mode = "unavailable"

    async def predict(
        self, image_bytes: bytes, research_session_id: UUID | None
    ) -> InferenceResult:
        del image_bytes, research_session_id
        raise ModelUnavailableError("No inference model is configured.")


class DemoMockInferenceAdapter:
    """Simulates only the request/response flow; it never fabricates a prediction."""

    model_available = False
    model_version = "demo-mock-v0"
    inference_mode = "simulated"

    async def predict(
        self, image_bytes: bytes, research_session_id: UUID | None
    ) -> InferenceResult:
        del image_bytes, research_session_id
        return InferenceResult(
            analysis_status=AnalysisStatus.INCONCLUSIVE,
            model_label=None,
            raw_model_score=None,
            model_version=self.model_version,
            inference_mode=InferenceMode.SIMULATED,
            warning=(
                "SIMULATED DEVELOPMENT RESPONSE. No model inference or morphology "
                "prediction was performed."
            ),
        )


class ConfiguredCloudAdapter:
    """Named provider boundary; live provider protocol/authentication is not implemented yet."""

    model_available = False
    model_version = None

    def __init__(self, provider: str) -> None:
        self.provider = provider
        self.inference_mode = "unavailable"

    async def predict(
        self, image_bytes: bytes, research_session_id: UUID | None
    ) -> InferenceResult:
        del image_bytes, research_session_id
        raise ModelUnavailableError(
            f"The {self.provider} adapter is scaffolded but not configured for live inference."
        )


def build_inference_adapter(settings: Settings) -> InferenceAdapter:
    if settings.enable_demo_mock:
        return DemoMockInferenceAdapter()
    if settings.inference_provider == "modelarts":
        from app.integrations.huawei_modelarts import HuaweiModelArtsAdapter

        return HuaweiModelArtsAdapter(settings)
    if settings.inference_provider == "ecs":
        from app.integrations.ecs_inference import HuaweiECSInferenceAdapter

        return HuaweiECSInferenceAdapter(settings)
    return UnavailableInferenceAdapter()
