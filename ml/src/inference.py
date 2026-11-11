from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ModelNotAvailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class CellPrediction:
    model_label: str
    raw_model_score: float
    model_version: str
    preprocessing: dict[str, object]


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
        from src.preprocessing import build_transforms

        self.torch = torch
        self.device = torch.device(device)
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.model_version = checkpoint["model_version"]
        self.label_names = checkpoint["label_names"]
        self.preprocessing = checkpoint["preprocessing"]
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
            scores = self.torch.softmax(logits, dim=1)[0]
            index = int(scores.argmax().item())
        return CellPrediction(
            model_label=self.label_names[index],
            raw_model_score=float(scores[index].item()),
            model_version=self.model_version,
            preprocessing=self.preprocessing,
        )
