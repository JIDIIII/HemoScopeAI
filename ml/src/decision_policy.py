"""Provisional Option B for the explicitly selected research checkpoint."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from numbers import Real


class InvalidScoreError(ValueError):
    pass


class PolicyBindingError(ValueError):
    pass


@dataclass(frozen=True)
class PolicyDecision:
    analysis_status: str
    all_score: float
    decision_policy_version: str
    message: str


@dataclass(frozen=True)
class OptionBPolicy:
    """Fixed/versioned rule; other checkpoints require separately reviewed policies."""

    version: str = field(default="hemoscope-option-b-v1", init=False)
    lower: float = field(default=0.30, init=False)
    upper: float = field(default=0.70, init=False)
    model_version: str = field(default="hemoscope-mobilenetv3-small-grouped-lowlr-v1", init=False)
    checkpoint_sha256: str = field(
        default="58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98", init=False
    )

    def check_binding(self, *, model_version: str, checkpoint_sha256: str) -> None:
        if model_version != self.model_version or checkpoint_sha256 != self.checkpoint_sha256:
            raise PolicyBindingError("Option B is not approved for this checkpoint/version.")

    def decide(
        self, all_score: float, *, model_version: str, checkpoint_sha256: str
    ) -> PolicyDecision:
        self.check_binding(model_version=model_version, checkpoint_sha256=checkpoint_sha256)
        if (
            isinstance(all_score, bool)
            or not isinstance(all_score, Real)
            or not math.isfinite(all_score)
            or not 0 <= all_score <= 1
        ):
            raise InvalidScoreError("Expected a finite ALL-class score between 0 and 1.")
        score = float(all_score)
        if score < self.lower:
            status = "analysis_complete"
            message = (
                "No model flag for this selected cell at the research threshold. "
                "This does not rule out disease."
            )
        elif score < self.upper:
            status = "inconclusive"
            message = (
                "The model cannot provide a clear result for this selected cell. "
                "Qualified review is required."
            )
        else:
            status = "review_required"
            message = "Morphology flag in the selected cell. Qualified review required."
        message += " Research and educational use only; this is not a diagnosis."
        return PolicyDecision(status, score, self.version, message)


OPTION_B_V1 = OptionBPolicy()
