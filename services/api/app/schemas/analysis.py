from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.quality import QualityRejectionReason, QualityStatus


class AnalysisStatus(StrEnum):
    RECAPTURE_REQUIRED = "recapture_required"
    INCONCLUSIVE = "inconclusive"
    REVIEW_REQUIRED = "review_required"
    ANALYSIS_COMPLETE = "analysis_complete"
    ERROR = "error"


class InferenceMode(StrEnum):
    REAL = "real"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"


class CropBounds(BaseModel):
    """Normalized crop rectangle within an uploaded source field."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def stays_within_image(self) -> "CropBounds":
        tolerance = 1e-9
        if self.x + self.width > 1 + tolerance or self.y + self.height > 1 + tolerance:
            raise ValueError("Crop bounds must stay within the source image.")
        return self


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_status: str
    api_version: str
    model_available: bool
    model_version: str | None = None
    inference_mode: InferenceMode


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: UUID
    request_id: str = Field(min_length=1, max_length=128)
    analysis_status: AnalysisStatus
    quality_status: QualityStatus
    rejection_reasons: list[QualityRejectionReason] = Field(default_factory=list)
    actionable_instructions: list[str] = Field(default_factory=list)
    model_label: str | None = None
    raw_model_score: float | None = Field(default=None, ge=0, le=1)
    model_version: str | None = None
    inference_mode: InferenceMode | None = None
    research_session_id: UUID | None = None
    warning: str


class SessionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    created_at: str
    quality_status: QualityStatus | None = None
    analysis_status: AnalysisStatus | None = None
    model_version: str | None = None
