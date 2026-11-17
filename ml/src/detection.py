"""Dataset and validation helpers for the BCCD WBC localization prototype."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms.functional import pil_to_tensor

CLASS_NAMES = ("Platelets", "RBC", "WBC")
CLASS_TO_INDEX = {name: index + 1 for index, name in enumerate(CLASS_NAMES)}
INDEX_TO_CLASS = {index: name for name, index in CLASS_TO_INDEX.items()}
ALLOWED_SPLITS = {"train", "val", "test"}


@dataclass(frozen=True)
class DetectionRecord:
    image_id: str
    image_path: Path
    split: str
    width: int
    height: int
    boxes: tuple[tuple[float, float, float, float], ...]
    labels: tuple[int, ...]


def load_detection_records(
    images_manifest: Path,
    annotations_manifest: Path,
    dataset_root: Path,
    *,
    include_test: bool = False,
) -> list[DetectionRecord]:
    """Load training/validation rows; omit held-out test annotations by default."""
    selected_splits = {"train", "val"} | ({"test"} if include_test else set())
    image_rows: dict[str, dict[str, str]] = {}
    with images_manifest.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            image_id = row["image_id"]
            if image_id in image_rows:
                raise ValueError(f"Duplicate image manifest row: {image_id}")
            if row["split"] not in ALLOWED_SPLITS:
                raise ValueError(f"Invalid split for {image_id}: {row['split']}")
            if row["split"] in selected_splits:
                image_rows[image_id] = row

    grouped_boxes: dict[
        str, list[tuple[tuple[float, float, float, float], int]]
    ] = defaultdict(list)
    with annotations_manifest.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            image_id = row["image_id"]
            if row["split"] not in selected_splits:
                continue
            if image_id not in image_rows:
                raise ValueError(f"Annotation refers to an unselected/unknown image: {image_id}")
            if row["split"] != image_rows[image_id]["split"]:
                raise ValueError(f"Split mismatch in annotation for {image_id}")
            try:
                label = CLASS_TO_INDEX[row["class_name"]]
            except KeyError as exc:
                raise ValueError(f"Unknown BCCD class: {row['class_name']}") from exc

            # Pascal VOC coordinates are 1-based and inclusive. Convert to the
            # zero-based continuous box convention used by TorchVision detectors.
            x_min = float(row["voc_xmin"]) - 1.0
            y_min = float(row["voc_ymin"]) - 1.0
            x_max = float(row["voc_xmax"])
            y_max = float(row["voc_ymax"])
            width = int(image_rows[image_id]["width"])
            height = int(image_rows[image_id]["height"])
            if not (0 <= x_min < x_max <= width and 0 <= y_min < y_max <= height):
                raise ValueError(
                    f"Converted box is out of bounds for {image_id}: "
                    f"{(x_min, y_min, x_max, y_max)}"
                )
            grouped_boxes[image_id].append(((x_min, y_min, x_max, y_max), label))

    dataset_root = dataset_root.expanduser().resolve()
    records: list[DetectionRecord] = []
    for image_id, row in sorted(image_rows.items()):
        relative_path = Path(row["image_path"])
        image_path = (dataset_root / relative_path).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Image referenced by BCCD manifest is missing: {image_path}")
        boxes_and_labels = grouped_boxes.get(image_id, [])
        expected_count = int(row["box_count"])
        if len(boxes_and_labels) != expected_count:
            raise ValueError(
                f"Manifest box count differs for {image_id}: "
                f"expected={expected_count}, found={len(boxes_and_labels)}"
            )
        records.append(
            DetectionRecord(
                image_id=image_id,
                image_path=image_path,
                split=row["split"],
                width=int(row["width"]),
                height=int(row["height"]),
                boxes=tuple(box for box, _ in boxes_and_labels),
                labels=tuple(label for _, label in boxes_and_labels),
            )
        )
    return records


class BCCDDetectionDataset(Dataset):
    def __init__(self, records: list[DetectionRecord]):
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        record = self.records[index]
        with Image.open(record.image_path) as source:
            image = pil_to_tensor(source.convert("RGB")).float().div_(255.0)
        target = {
            "boxes": torch.tensor(record.boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.tensor(record.labels, dtype=torch.int64),
        }
        return image, target, record.image_id


def detection_collate(batch):
    images, targets, image_ids = zip(*batch, strict=True)
    return list(images), list(targets), list(image_ids)


def box_iou(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    x_min = max(left[0], right[0])
    y_min = max(left[1], right[1])
    x_max = min(left[2], right[2])
    y_max = min(left[3], right[3])
    intersection = max(0.0, x_max - x_min) * max(0.0, y_max - y_min)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union > 0 else 0.0


def average_precision_at_iou(
    predictions: list[tuple[float, str, tuple[float, ...]]],
    ground_truth: dict[str, list[tuple[float, ...]]],
    *,
    iou_threshold: float,
) -> float:
    positive_count = sum(len(boxes) for boxes in ground_truth.values())
    if positive_count == 0:
        return 0.0
    ordered = sorted(predictions, key=lambda item: item[0], reverse=True)
    matched: dict[str, set[int]] = defaultdict(set)
    true_positives: list[int] = []
    false_positives: list[int] = []
    for _, image_id, predicted_box in ordered:
        candidates = ground_truth.get(image_id, [])
        best_index = max(
            range(len(candidates)),
            key=lambda index: box_iou(predicted_box, candidates[index]),
            default=-1,
        )
        if (
            best_index >= 0
            and best_index not in matched[image_id]
            and box_iou(predicted_box, candidates[best_index]) >= iou_threshold
        ):
            matched[image_id].add(best_index)
            true_positives.append(1)
            false_positives.append(0)
        else:
            true_positives.append(0)
            false_positives.append(1)

    cumulative_tp: list[int] = []
    cumulative_fp: list[int] = []
    tp_total = fp_total = 0
    for tp, fp in zip(true_positives, false_positives, strict=True):
        tp_total += tp
        fp_total += fp
        cumulative_tp.append(tp_total)
        cumulative_fp.append(fp_total)
    recalls = [tp / positive_count for tp in cumulative_tp]
    precisions = [
        tp / (tp + fp) if tp + fp else 0.0
        for tp, fp in zip(cumulative_tp, cumulative_fp, strict=True)
    ]
    interpolated_precision = []
    for target_index in range(101):
        target_recall = target_index / 100.0
        interpolated_precision.append(
            max(
                (
                    precision
                    for recall, precision in zip(recalls, precisions, strict=True)
                    if recall >= target_recall
                ),
                default=0.0,
            )
        )
    return sum(interpolated_precision) / 101.0


def evaluate_detector(
    model,
    data_loader,
    device: torch.device,
    *,
    iou_threshold: float,
    candidate_score_threshold: float,
) -> dict[str, object]:
    model.eval()
    ground_truth: dict[int, dict[str, list[tuple[float, ...]]]] = {
        label: defaultdict(list) for label in INDEX_TO_CLASS
    }
    predictions: dict[int, list[tuple[float, str, tuple[float, ...]]]] = {
        label: [] for label in INDEX_TO_CLASS
    }
    image_ids: set[str] = set()
    with torch.inference_mode():
        for images, targets, batch_image_ids in data_loader:
            outputs = model([image.to(device) for image in images])
            for target, output, image_id in zip(targets, outputs, batch_image_ids, strict=True):
                image_ids.add(image_id)
                for box, label in zip(
                    target["boxes"].tolist(), target["labels"].tolist(), strict=True
                ):
                    ground_truth[label][image_id].append(tuple(float(value) for value in box))
                output_boxes = output["boxes"].detach().cpu().tolist()
                output_labels = output["labels"].detach().cpu().tolist()
                output_scores = output["scores"].detach().cpu().tolist()
                for box, label, score in zip(
                    output_boxes, output_labels, output_scores, strict=True
                ):
                    if label in predictions:
                        predictions[label].append(
                            (float(score), image_id, tuple(float(value) for value in box))
                        )

    ap_by_class = {
        INDEX_TO_CLASS[label]: average_precision_at_iou(
            predictions[label], ground_truth[label], iou_threshold=iou_threshold
        )
        for label in INDEX_TO_CLASS
    }
    wbc_label = CLASS_TO_INDEX["WBC"]
    wbc_predictions = sorted(
        (item for item in predictions[wbc_label] if item[0] >= candidate_score_threshold),
        key=lambda item: item[0],
        reverse=True,
    )
    matched_wbc: dict[str, set[int]] = defaultdict(set)
    true_positive_count = false_positive_count = 0
    wbc_positive_count = sum(len(boxes) for boxes in ground_truth[wbc_label].values())
    for _, image_id, predicted_box in wbc_predictions:
        candidates = ground_truth[wbc_label].get(image_id, [])
        best_index = max(
            range(len(candidates)),
            key=lambda index: box_iou(predicted_box, candidates[index]),
            default=-1,
        )
        if (
            best_index >= 0
            and best_index not in matched_wbc[image_id]
            and box_iou(predicted_box, candidates[best_index]) >= iou_threshold
        ):
            matched_wbc[image_id].add(best_index)
            true_positive_count += 1
        else:
            false_positive_count += 1
    false_negative_count = max(0, wbc_positive_count - true_positive_count)
    return {
        "sample_count": len(image_ids),
        "iou_threshold": iou_threshold,
        "candidate_score_threshold": candidate_score_threshold,
        "ap50_by_class": ap_by_class,
        "mean_ap50": sum(ap_by_class.values()) / max(len(ap_by_class), 1),
        "wbc_ap50": ap_by_class["WBC"],
        "wbc_precision_at_threshold": true_positive_count
        / max(true_positive_count + false_positive_count, 1),
        "wbc_recall_at_threshold": true_positive_count / max(wbc_positive_count, 1),
        "wbc_false_positives_per_image": false_positive_count / max(len(image_ids), 1),
        "wbc_true_positives": true_positive_count,
        "wbc_false_positives": false_positive_count,
        "wbc_false_negatives": false_negative_count,
        "wbc_ground_truth_boxes": wbc_positive_count,
    }
