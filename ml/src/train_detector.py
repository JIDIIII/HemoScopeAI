"""Train a research-only BCCD cell-localization detector (train/validation only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import time
from collections import Counter
from pathlib import Path

import torch
import torchvision
import yaml
from PIL import Image
from torch.utils.data import DataLoader
from torchvision.models import MobileNet_V3_Large_Weights
from torchvision.models.detection import ssdlite320_mobilenet_v3_large

from src.detection import (
    CLASS_NAMES,
    CLASS_TO_INDEX,
    INDEX_TO_CLASS,
    BCCDDetectionDataset,
    detection_collate,
    evaluate_detector,
    load_detection_records,
)


def select_device(requested: str) -> torch.device:
    available = {
        "cuda": torch.cuda.is_available(),
        "mps": torch.backends.mps.is_available(),
        "cpu": True,
    }
    if requested == "auto":
        return torch.device(next(name for name, enabled in available.items() if enabled))
    if requested not in available or not available[requested]:
        raise ValueError(f"Requested training device is unavailable: {requested}")
    return torch.device(requested)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_loader(dataset, batch_size: int, workers: int, *, shuffle: bool, device: torch.device):
    options = {}
    if workers > 0:
        options = {"persistent_workers": True, "prefetch_factor": 2}
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=workers,
        pin_memory=device.type == "cuda",
        collate_fn=detection_collate,
        **options,
    )


def build_model(model_config: dict[str, object]):
    backbone_weights = (
        MobileNet_V3_Large_Weights.DEFAULT
        if bool(model_config.get("pretrained_backbone", True))
        else None
    )
    # The detector head is initialized for the three BCCD classes plus background;
    # only the MobileNetV3 backbone starts from ImageNet weights.
    return ssdlite320_mobilenet_v3_large(
        weights=None,
        weights_backbone=backbone_weights,
        num_classes=len(CLASS_NAMES) + 1,
        trainable_backbone_layers=int(model_config.get("trainable_backbone_layers", 3)),
    )


def summarize_records(records) -> dict[str, object]:
    splits = {}
    for split in ("train", "val"):
        split_records = [record for record in records if record.split == split]
        counts: Counter[str] = Counter()
        for record in split_records:
            for label in record.labels:
                counts[INDEX_TO_CLASS[label]] += 1
        splits[split] = {
            "images": len(split_records),
            "boxes": sum(counts.values()),
            "box_count_by_class": dict(sorted(counts.items())),
        }
    return splits


def check_dataset(records) -> dict[str, object]:
    """Decode selected train/validation images and verify dimensions without a model."""
    decoded_images = 0
    for record in records:
        with Image.open(record.image_path) as image:
            if image.size != (record.width, record.height):
                raise ValueError(
                    f"Image dimensions changed for {record.image_id}: "
                    f"manifest={(record.width, record.height)}, actual={image.size}"
                )
            image.verify()
        decoded_images += 1
    return {"decoded_train_validation_images": decoded_images}


def synchronize(device: torch.device) -> None:
    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize()


def run_training(config_path: Path, *, check_data_only: bool = False) -> None:
    ml_root = Path(__file__).resolve().parents[1]
    config_path = config_path.expanduser()
    if not config_path.is_absolute():
        config_path = ml_root / config_path
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    dataset_config = config["dataset"]
    model_config = config["model"]
    training_config = config["training"]
    metric_config = config["validation"]

    def resolve_ml_path(value: str) -> Path:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (ml_root / path).resolve()

    images_manifest = resolve_ml_path(dataset_config["images_manifest"])
    annotations_manifest = resolve_ml_path(dataset_config["annotations_manifest"])
    split_summary = resolve_ml_path(dataset_config["split_summary"])
    dataset_root = Path(dataset_config["root"]).expanduser().resolve()
    output_dir = resolve_ml_path(training_config["output_dir"])

    for required in (images_manifest, annotations_manifest, split_summary):
        if not required.is_file():
            raise FileNotFoundError(f"Required prepared BCCD file is missing: {required}")
    split_data = json.loads(split_summary.read_text(encoding="utf-8"))
    if split_data.get("validation", {}).get("subject_or_slide_independence_verified") is True:
        raise ValueError("This prototype does not support a patient-independent split claim.")

    records = load_detection_records(
        images_manifest,
        annotations_manifest,
        dataset_root,
        include_test=False,
    )
    split_counts = summarize_records(records)
    if not records or not split_counts["train"]["images"] or not split_counts["val"]["images"]:
        raise ValueError("BCCD train and validation splits must both contain images.")
    if split_counts["train"]["box_count_by_class"].get("WBC", 0) == 0:
        raise ValueError("Training split must contain WBC boxes.")
    if split_counts["val"]["box_count_by_class"].get("WBC", 0) == 0:
        raise ValueError("Validation split must contain WBC boxes.")

    if check_data_only:
        image_check = check_dataset(records)
        print(
            json.dumps(
                {
                    "stage": "detector_data_check_passed",
                    "training_started": False,
                    "model_created": False,
                    "test_evaluated": False,
                    "split_counts": split_counts,
                    "image_check": image_check,
                    "data_root": str(dataset_root),
                },
                indent=2,
            ),
            flush=True,
        )
        return

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite non-empty experiment directory: {output_dir}. "
            "Set a fresh output_dir in the config for each run."
        )

    seed = int(training_config["seed"])
    seed_everything(seed)
    device = select_device(str(training_config.get("device", "auto")))
    train_records = [record for record in records if record.split == "train"]
    validation_records = [record for record in records if record.split == "val"]
    train_loader = make_loader(
        BCCDDetectionDataset(train_records),
        int(training_config["batch_size"]),
        int(training_config.get("num_workers", 0)),
        shuffle=True,
        device=device,
    )
    validation_loader = make_loader(
        BCCDDetectionDataset(validation_records),
        int(training_config["batch_size"]),
        int(training_config.get("num_workers", 0)),
        shuffle=False,
        device=device,
    )

    print(
        json.dumps(
            {
                "stage": "detector_ready",
                "device": str(device),
                "train_images": len(train_records),
                "validation_images": len(validation_records),
                "test_evaluated": False,
            }
        ),
        flush=True,
    )
    model = build_model(model_config).to(device)
    optimizer = torch.optim.SGD(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=float(training_config["learning_rate"]),
        momentum=float(training_config["momentum"]),
        weight_decay=float(training_config["weight_decay"]),
    )
    scheduler = torch.optim.lr_scheduler.MultiStepLR(
        optimizer,
        milestones=[int(epoch) for epoch in training_config["lr_milestones"]],
        gamma=float(training_config["lr_gamma"]),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run-config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )

    best_wbc_ap50 = -math.inf
    best_epoch = 0
    best_validation_metrics: dict[str, object] | None = None
    history_path = output_dir / "history.jsonl"
    for epoch in range(1, int(training_config["epochs"]) + 1):
        synchronize(device)
        epoch_started = time.perf_counter()
        model.train()
        loss_total = 0.0
        for batch_index, (images, targets, _) in enumerate(train_loader, start=1):
            images = [image.to(device) for image in images]
            device_targets = [
                {name: value.to(device) for name, value in target.items()}
                for target in targets
            ]
            optimizer.zero_grad(set_to_none=True)
            loss_dict = model(images, device_targets)
            loss = sum(loss_dict.values())
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"Non-finite detector loss at epoch {epoch}, batch {batch_index}."
                )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), float(training_config["gradient_clip_norm"])
            )
            optimizer.step()
            loss_total += float(loss.detach().cpu())
            should_log = (
                batch_index % int(training_config["log_every_batches"]) == 0
                or batch_index == len(train_loader)
            )
            if should_log:
                print(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "batch": batch_index,
                            "batches": len(train_loader),
                            "mean_batch_loss": round(loss_total / batch_index, 5),
                        }
                    ),
                    flush=True,
                )

        synchronize(device)
        validation_metrics = evaluate_detector(
            model,
            validation_loader,
            device,
            iou_threshold=float(metric_config["iou_threshold"]),
            candidate_score_threshold=float(metric_config["candidate_score_threshold"]),
        )
        scheduler.step()
        epoch_seconds = time.perf_counter() - epoch_started
        record = {
            "epoch": epoch,
            "epoch_seconds": round(epoch_seconds, 2),
            "mean_train_loss": round(loss_total / max(len(train_loader), 1), 6),
            "learning_rate": optimizer.param_groups[0]["lr"],
            "validation_metrics": validation_metrics,
        }
        with history_path.open("a", encoding="utf-8") as history:
            history.write(json.dumps(record, sort_keys=True) + "\n")
        print(json.dumps(record), flush=True)

        if float(validation_metrics["wbc_ap50"]) > best_wbc_ap50:
            best_wbc_ap50 = float(validation_metrics["wbc_ap50"])
            best_epoch = epoch
            best_validation_metrics = validation_metrics
            checkpoint_path = output_dir / "best-checkpoint.pt"
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "model_version": model_config["version"],
                    "class_names": list(CLASS_NAMES),
                    "class_to_index": CLASS_TO_INDEX,
                    "input_size": int(model_config["input_size"]),
                    "best_epoch": best_epoch,
                    "best_validation_metrics": validation_metrics,
                    "config": config,
                },
                checkpoint_path,
            )

    checkpoint_path = output_dir / "best-checkpoint.pt"
    metadata = {
        "model_version": model_config["version"],
        "architecture": model_config["architecture"],
        "class_names": list(CLASS_NAMES),
        "class_to_index": CLASS_TO_INDEX,
        "input_size": int(model_config["input_size"]),
        "torch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "python_version": platform.python_version(),
        "device": str(device),
        "best_epoch_selected_by": "validation WBC AP at IoU 0.50",
        "best_epoch": best_epoch,
        "best_validation_metrics": best_validation_metrics,
        "dataset": {
            "images_manifest_sha256": sha256_file(images_manifest),
            "annotations_manifest_sha256": sha256_file(annotations_manifest),
            "split_summary_sha256": sha256_file(split_summary),
            "split_counts_used": split_counts,
            "test_evaluated": False,
            "subject_or_slide_independence_verified": False,
        },
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "config": config,
        "note": (
            "Research-only WBC localization prototype. BCCD does not identify leukemia, "
            "and its source split is not verified as patient-independent."
        ),
    }
    (output_dir / "model-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "stage": "detector_training_complete",
                "model_version": model_config["version"],
                "best_epoch": best_epoch,
                "best_validation_metrics": metadata["best_validation_metrics"],
                "test_evaluated": False,
                "checkpoint": str(checkpoint_path),
            },
            indent=2,
        ),
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/bccd-ssdlite-wbc-v1.yaml"))
    parser.add_argument(
        "--check-data-only",
        action="store_true",
        help="Decode train/validation images and validate manifests without constructing a model.",
    )
    args = parser.parse_args()
    run_training(args.config, check_data_only=args.check_data_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
