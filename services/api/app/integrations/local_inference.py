from __future__ import annotations

import asyncio
import logging
import sys
from io import BytesIO
from pathlib import Path
from threading import Lock
from types import ModuleType
from uuid import UUID

from app.core.config import Settings
from app.schemas.analysis import AnalysisStatus, InferenceMode
from app.services.inference import (
    InferenceResult,
    InvalidInferenceResultError,
    ModelUnavailableError,
)

logger = logging.getLogger(__name__)


class LocalInferenceAdapter:
    """Runs the versioned local handoff bundle on CPU; it never downloads weights."""

    inference_mode = InferenceMode.REAL

    def __init__(self, settings: Settings) -> None:
        self.bundle_dir = settings.local_inference_bundle_dir.expanduser().resolve()
        self.checkpoint_path = self.bundle_dir / "model" / "checkpoint.pt"
        self.device = settings.local_inference_device
        self._classifier = None
        self._bundle: ModuleType | None = None
        self._bundle_error: Exception | None = None
        self._load_lock = Lock()
        try:
            self._load_classifier()
        except Exception as exc:
            # Keep the API available; /analyze will fail closed with model_unavailable.
            self._bundle_error = exc
            logger.warning("Local inference is unavailable: %s", exc)

    @property
    def model_available(self) -> bool:
        return self._classifier is not None

    @property
    def model_version(self) -> str | None:
        return self._classifier.model_version if self._classifier is not None else None

    def _load_classifier(self) -> None:
        if self._classifier is not None:
            return
        with self._load_lock:
            if self._classifier is not None:
                return
            if not self.checkpoint_path.is_file():
                raise FileNotFoundError("The configured local inference checkpoint is missing.")
            bundle_path = str(self.bundle_dir)
            if bundle_path not in sys.path:
                sys.path.insert(0, bundle_path)
            import hemoscope_inference
            from hemoscope_inference import CellClassifier

            if not Path(hemoscope_inference.__file__).resolve().is_relative_to(self.bundle_dir):
                raise ImportError("The inference package did not load from the configured bundle.")
            self._bundle = hemoscope_inference
            self._classifier = CellClassifier(self.checkpoint_path, device=self.device)

    async def predict(
        self, image_bytes: bytes, research_session_id: UUID | None
    ) -> InferenceResult:
        del research_session_id
        try:
            self._load_classifier()
        except Exception as exc:
            raise ModelUnavailableError(
                "The local inference bundle or checkpoint is unavailable."
            ) from (self._bundle_error or exc)
        self._bundle_error = None
        try:
            return await asyncio.to_thread(self._predict_sync, image_bytes)
        except ModelUnavailableError:
            raise
        except Exception as exc:
            raise InvalidInferenceResultError(
                "The local model could not produce a valid policy result."
            ) from exc

    def _predict_sync(self, image_bytes: bytes) -> InferenceResult:
        from PIL import Image

        assert self._classifier is not None
        assert self._bundle is not None
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                with self._load_lock:
                    result = self._classifier.predict_with_policy(
                        image.convert("RGB"),
                        quality_accepted=True,
                        crop_confirmed=True,
                    )
        except Exception as exc:
            raise InvalidInferenceResultError(
                "Could not decode or classify the accepted crop."
            ) from exc

        warning = result.decision.message
        if result.decision.analysis_status == "analysis_complete":
            warning = (
                "No model flag at this research threshold. This does not rule out disease. "
                "Research and educational use only; this is not a diagnosis."
            )

        return InferenceResult(
            analysis_status=AnalysisStatus(result.decision.analysis_status),
            model_label=result.prediction.model_label,
            raw_model_score=result.prediction.raw_model_score,
            model_version=result.prediction.model_version,
            inference_mode=InferenceMode.REAL,
            warning=warning,
            all_score=result.prediction.all_score,
            decision_policy_version=result.decision.decision_policy_version,
        )
