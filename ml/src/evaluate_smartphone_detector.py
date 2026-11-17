"""Check BCCD WBC localization on NIH/NLM smartphone polygon annotations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import torch
import yaml
from PIL import Image
from torch.utils.data import DataLoader
from torchvision.transforms.functional import pil_to_tensor

from src.detection import (
    CLASS_TO_INDEX,
    DetectionRecord,
    detection_collate,
    evaluate_detector,
)
from src.train_detector import build_model


def parse_polygon_annotation(
    path: Path,
) -> tuple[int, int, list[tuple[float, float, float, float]]]:
    """Return image dimensions and WBC polygon bounding boxes from one NIH/NLM file."""
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.reader(source)
        header = next(reader, None)
        if header is None or len(header) < 3:
            raise ValueError(f"Missing image header in annotation: {path}")
        try:
            expected_objects, width, height = map(int, header[:3])
        except ValueError as exc:
            raise ValueError(f"Invalid image header in annotation: {path}") from exc
        if min(width, height) <= 0:
            raise ValueError(f"Invalid image dimensions in annotation: {path}")

        row_count = 0
        wbc_boxes = []
        for row in reader:
            if not row:
                continue
            row_count += 1
            if len(row) < 5:
                raise ValueError(f"Malformed object row in annotation: {path}")
            if row[1] != "White_Blood_Cell":
                continue
            if row[3] != "Polygon":
                raise ValueError(f"WBC annotation is not a polygon: {path}")
            try:
                point_count = int(row[4])
                coordinates = [float(value) for value in row[5:]]
            except ValueError as exc:
                raise ValueError(f"Invalid WBC polygon coordinates: {path}") from exc
            if point_count < 3 or len(coordinates) != point_count * 2:
                raise ValueError(f"WBC polygon point count is inconsistent: {path}")
            xs, ys = coordinates[::2], coordinates[1::2]
            out_of_bounds = any(
                not 0 <= x <= width or not 0 <= y <= height
                for x, y in zip(xs, ys, strict=True)
            )
            if out_of_bounds:
                raise ValueError(f"WBC polygon point is outside image bounds: {path}")
            box = (min(xs), min(ys), max(xs), max(ys))
            if box[0] >= box[2] or box[1] >= box[3]:
                raise ValueError(f"WBC polygon has zero area: {path}")
            wbc_boxes.append(box)
        if row_count != expected_objects:
            raise ValueError(
                f"Annotation object count differs in {path}: "
                f"header={expected_objects}, rows={row_count}"
            )
    return width, height, wbc_boxes


class SmartphonePolygonDataset(torch.utils.data.Dataset):
    def __init__(self, records: list[DetectionRecord]):
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        record = self.records[index]
        with Image.open(record.image_path) as source:
            image = source.convert("RGB")
            if image.size != (record.width, record.height):
                raise ValueError(
                    f"Image/annotation dimensions differ for anonymous image {record.image_id}"
                )
            tensor = pil_to_tensor(image).float().div_(255.0)
        target = {
            "boxes": torch.tensor(record.boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.tensor(record.labels, dtype=torch.int64),
        }
        return tensor, target, record.image_id


def load_smartphone_records(dataset_root: Path) -> list[DetectionRecord]:
    """Load polygon-set fields with WBC boxes only; do not expose patient folder names."""
    dataset_root = dataset_root.expanduser().resolve()
    annotations = sorted(dataset_root.glob("*/GT/*.txt"))
    if not annotations:
        raise FileNotFoundError(f"No polygon annotations found under {dataset_root}")
    records = []
    for index, annotation in enumerate(annotations):
        image_path = annotation.parent.parent / "Img" / f"{annotation.stem}.jpg"
        if not image_path.is_file():
            raise FileNotFoundError(f"Image for polygon annotation is missing: {image_path}")
        width, height, boxes = parse_polygon_annotation(annotation)
        records.append(
            DetectionRecord(
                image_id=f"phone-field-{index:04d}",
                image_path=image_path,
                split="external_check",
                width=width,
                height=height,
                boxes=tuple(boxes),
                labels=tuple(CLASS_TO_INDEX["WBC"] for _ in boxes),
            )
        )
    return records


def evaluate(run_dir: Path, dataset_root: Path, output: Path) -> dict[str, object]:
    run_dir = run_dir.expanduser().resolve()
    dataset_root = dataset_root.expanduser().resolve()
    output = output.expanduser().resolve()
    checkpoint_path = run_dir / "best-checkpoint.pt"
    config_path = run_dir / "run-config.yaml"
    if not checkpoint_path.is_file() or not config_path.is_file():
        raise FileNotFoundError(f"Detector run is incomplete: {run_dir}")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an evaluation report: {output}")

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model_config = dict(config["model"])
    # The pretrained-backbone setting controls SSDlite's reduced-tail shape, so
    # preserve it when rebuilding the exact architecture. Block any cache miss
    # from reaching the network; the backbone weights must already be cached.
    with patch("socket.socket.connect", side_effect=AssertionError("Network disabled")):
        model = build_model(model_config)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    torch.set_num_threads(1)

    records = load_smartphone_records(dataset_root)
    dataset = SmartphonePolygonDataset(records)
    loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0,
        collate_fn=detection_collate,
    )
    metrics = evaluate_detector(
        model,
        loader,
        torch.device("cpu"),
        iou_threshold=0.5,
        candidate_score_threshold=float(config["validation"]["candidate_score_threshold"]),
    )
    report = {
        "evaluation": "external_domain_check_not_training_or_threshold_selection",
        "source": "NIH/NLM Thin Blood Smear smartphone dataset, Polygon Set",
        "image_count": len(records),
        "patient_folder_count": len({r.image_path.parent.parent.name for r in records}),
        "wbc_ground_truth_polygons": sum(len(r.boxes) for r in records),
        "target_label_scope": "generic White_Blood_Cell localization only; no leukemia labels",
        "detector_model_version": checkpoint["model_version"],
        "checkpoint_sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        "input_preprocessing": (
            "RGB float [0,1]; TorchVision detector preprocessing; no EXIF rotation"
        ),
        "iou_threshold": 0.5,
        "candidate_score_threshold": metrics["candidate_score_threshold"],
        "wbc_ap50": metrics["wbc_ap50"],
        "wbc_precision_at_threshold": metrics["wbc_precision_at_threshold"],
        "wbc_recall_at_threshold": metrics["wbc_recall_at_threshold"],
        "wbc_false_positives_per_image": metrics["wbc_false_positives_per_image"],
        "wbc_true_positives": metrics["wbc_true_positives"],
        "wbc_false_positives": metrics["wbc_false_positives"],
        "wbc_false_negatives": metrics["wbc_false_negatives"],
        "limitations": [
            "This is a small cross-domain check, not a representative target-phone study.",
            "The source images concern malaria and do not establish leukemia status.",
            "Polygon bounding boxes are an approximation of the WBC outlines.",
            "Do not tune on this check or wire this detector into the app based on it.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument(
        "--run-dir", type=Path, default=Path("artifacts/bccd-ssdlite-wbc-v1")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/diagnostics/bccd-smartphone-check-v1.json")
    )
    args = parser.parse_args()
    evaluate(args.run_dir, args.dataset_root, args.output)


if __name__ == "__main__":
    main()
