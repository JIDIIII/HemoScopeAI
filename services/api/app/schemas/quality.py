from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QualityStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CaptureMetadata(BaseModel):
    """Non-identifying numeric setup metadata. No names, slide labels, or operator IDs."""

    model_config = ConfigDict(extra="forbid")

    objective_magnification: int | None = Field(default=None, ge=1, le=200)
    capture_sequence_index: int | None = Field(default=None, ge=0, le=10000)


class QualityMeasurements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: int
    height: int
    file_format: str
    blur_score: float = Field(description="Variance of Laplacian; development heuristic.")
    mean_brightness: float = Field(description="Mean grayscale intensity from 0 to 255.")
    overexposed_fraction: float = Field(ge=0, le=1)
    underexposed_fraction: float = Field(ge=0, le=1)


class QualityRejectionReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    instructions: str


class QualityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acceptable: bool
    quality_status: QualityStatus
    measurements: QualityMeasurements
    rejection_reasons: list[QualityRejectionReason]
    actionable_instructions: list[str]
