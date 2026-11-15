from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from src.decision_policy import OPTION_B_V1, OptionBPolicy, PolicyDecision


class ModelNotAvailableError(RuntimeError):
    pass


class InvalidModelOutputError(RuntimeError):
    pass


class InferencePreconditionError(ValueError):
    pass


@dataclass(frozen=True)
class CellPrediction:
    model_label: str
    raw_model_score: float
    model_version: str
    preprocessing: dict[str, object]
    all_score: float


@dataclass(frozen=True)
class PolicyPrediction:
    prediction: CellPrediction
    decision: PolicyDecision
    checkpoint_sha256: str


class CellClassifier:
    """Loads a locally supplied checkpoint; this module never downloads weights."""

    def __init__(self, checkpoint_path: Path, device: str = "cpu") -> None:
        if not checkpoint_path.is_file():
            raise ModelNotAvailableError(
                f"No trained model checkpoint is available at {checkpoint_path}."
            )
        try:
            import torch
        except ImportError as exc:
            raise ModelNotAvailableError(
                'Install the ML training dependencies with: python -m pip install -e ".[train]"'
            ) from exc

        from src.model import create_model
        from src.preprocessing import PreprocessingMetadata, build_transforms

        self.torch = torch
        self.device = torch.device(device)
        self.checkpoint_sha256 = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        self.model_version = checkpoint["model_version"]
        self.label_names = checkpoint["label_names"]
        if (
            len(self.label_names) != 2
            or set(self.label_names) != {"all", "hem"}
            or checkpoint.get("positive_label") != "all"
        ):
            raise InvalidModelOutputError("Checkpoint must identify ALL-positive binary classes.")
        self.all_index = self.label_names.index("all")
        self.preprocessing = checkpoint["preprocessing"]
        expected = PreprocessingMetadata(image_size=int(self.preprocessing["image_size"])).to_dict()
        if json.dumps(self.preprocessing, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise InvalidModelOutputError(
                "Checkpoint preprocessing is incompatible with this loader."
            )
        self.transform = build_transforms(int(self.preprocessing["image_size"]))
        self.model = create_model(num_classes=len(self.label_names), pretrained=False)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(self.device).eval()

    def predict(self, image):
        from PIL import Image

        if isinstance(image, (str, Path)):
            with Image.open(image) as source:
                tensor = self.transform(source.convert("RGB"))
        else:
            tensor = self.transform(image.convert("RGB"))
        with self.torch.no_grad():
            logits = self.model(tensor.unsqueeze(0).to(self.device))
            if (
                not isinstance(logits, self.torch.Tensor)
                or tuple(logits.shape) != (1, 2)
                or not logits.is_floating_point()
                or not self.torch.isfinite(logits).all().item()
            ):
                raise InvalidModelOutputError("Expected two finite class logits for one image.")
            scores = self.torch.softmax(logits, dim=1)[0]
            if not self.torch.isfinite(scores).all().item():
                raise InvalidModelOutputError("Model scores are not finite.")
            index = int(scores.argmax().item())
        return CellPrediction(
            model_label=self.label_names[index],
            raw_model_score=float(scores[index].item()),
            model_version=self.model_version,
            preprocessing=self.preprocessing,
            all_score=float(scores[self.all_index].item()),
        )

    def predict_with_policy(
        self,
        image,
        *,
        quality_accepted: bool,
        crop_confirmed: bool,
        policy: OptionBPolicy = OPTION_B_V1,
    ) -> PolicyPrediction:
        """Apply Option B only after the caller has verified quality and crop confirmation.

        These flags do not perform quality checks or establish biological suitability.
        The backend remains responsible for its rejection/error response handling.
        """
        if quality_accepted is not True or crop_confirmed is not True:
            raise InferencePreconditionError(
                "Quality acceptance and crop confirmation are required."
            )
        policy.check_binding(
            model_version=self.model_version, checkpoint_sha256=self.checkpoint_sha256
        )
        prediction = self.predict(image)
        decision = policy.decide(
            prediction.all_score,
            model_version=self.model_version,
            checkpoint_sha256=self.checkpoint_sha256,
        )
        return PolicyPrediction(prediction, decision, self.checkpoint_sha256)
