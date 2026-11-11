from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quality import QualityStatus


class AnalysisStatus(StrEnum):
    RECAPTURE_REQUIRED = "recapture_required"
    INCONCLUSIVE = "inconclusive"
    REVIEW_REQUIRED = "review_required"
    ANALYSIS_COMPLETE = "analysis_complete"
    ERROR = "error"


class InferenceMode(StrEnum):
    REAL = "real"
    SIMULATED = "simulated"


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_status: str
    api_version: str
    model_available: bool
    model_version: str | None = None
    inference_mode: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: UUID
    analysis_status: AnalysisStatus
    quality_status: QualityStatus
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
