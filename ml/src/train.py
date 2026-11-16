from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import time
from pathlib import Path

import numpy as np
import torch
import torchvision
import yaml
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.dataset import DatasetRecord, load_manifest
from src.evaluate import compute_metrics
from src.model import create_model
from src.preprocessing import PreprocessingMetadata, build_transforms
from src.split_config import resolve_split


def select_device(requested: str = "auto") -> torch.device:
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


def make_loader(dataset, batch_size: int, workers: int, *, shuffle: bool, device):
    options = {}
    if workers > 0:
        options = {"persistent_workers": True, "prefetch_factor": 2}
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=workers,
        pin_memory=device.type == "cuda",
        **options,
    )


def synchronize(device) -> None:
    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize()


class CellDataset(Dataset):
    def __init__(self, records: list[DatasetRecord], label_to_index: dict[str, int], transform):
        self.records = records
        self.label_to_index = label_to_index
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        record = self.records[index]
        with Image.open(record.image_path) as source:
            image = source.convert("RGB")
        return self.transform(image), self.label_to_index[record.label]


def evaluate_loader(model, loader, device, loss_function, positive_index: int):
    model.eval()
    total_loss = 0.0
    targets: list[int] = []
    predictions: list[int] = []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            total_loss += float(loss_function(logits, labels).item()) * len(labels)
            predictions.extend(logits.argmax(dim=1).cpu().tolist())
            targets.extend(labels.cpu().tolist())
    metrics = compute_metrics(targets, predictions, positive_class=positive_index)
    metrics["mean_loss"] = total_loss / max(len(targets), 1)
    return metrics


def run_training(config_path: Path, *, evaluate_only: bool = False, check_data_only: bool = False):
    started = time.perf_counter()
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    root = Path(__file__).resolve().parents[1]
    dataset_config = config["dataset"]
    training_config = config["training"]
    model_config = config["model"]
    if evaluate_only and check_data_only:
        raise ValueError("Choose evaluation or a data-only check, not both.")
    device = None if check_data_only else select_device(str(training_config.get("device", "auto")))
    print(
        json.dumps({"stage": "dataset_audit", "device": str(device) if device else None}),
        flush=True,
    )
    output_dir = (root / training_config["output_dir"]).resolve()
    best_checkpoint = output_dir / "best-checkpoint.pt"
    if not evaluate_only and not check_data_only and best_checkpoint.exists():
        raise FileExistsError(
            f"Checkpoint already exists in {output_dir}. Choose a new output_dir for a new run."
        )
    if evaluate_only and not best_checkpoint.is_file():
        raise FileNotFoundError(f"No checkpoint to evaluate: {best_checkpoint}")
    image_root = (root / dataset_config["image_root"]).resolve()
    manifest_path = (root / dataset_config["manifest"]).resolve()
    records = load_manifest(manifest_path, image_root)
    partitions, split_contents, split_provenance, snapshots = resolve_split(
        records, dataset_config, root, int(training_config["seed"])
    )
    train_records, validation_records, test_records = partitions
    split_manifest_sha256 = hashlib.sha256(split_contents).hexdigest()
    if check_data_only:
        report = {
            "stage": "data_check_passed",
            "training_started": False,
            "model_created": False,
            "output_dir": str(output_dir),
            "split_manifest_sha256": split_manifest_sha256,
            "split_provenance": split_provenance,
        }
        print(json.dumps(report, indent=2), flush=True)
        return report
    split_path = output_dir / "split-manifest.csv"
    if not evaluate_only:
        split_path.parent.mkdir(parents=True, exist_ok=True)
        split_path.write_bytes(split_contents)
        for name, source in snapshots.items():
            (output_dir / name).write_bytes(source.read_bytes())

    seed = int(training_config["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    label_names = sorted({record.label for record in records})
    if len(label_names) != 2:
        raise ValueError("The initial binary baseline requires exactly two manifest labels.")
    label_to_index = {label: index for index, label in enumerate(label_names)}
    if model_config["positive_label"] not in label_to_index:
        raise ValueError("Configured positive_label is absent from the manifest.")
    positive_index = label_to_index[model_config["positive_label"]]
    image_size = int(model_config["image_size"])
    train_dataset = CellDataset(
        train_records, label_to_index, build_transforms(image_size, training=True)
    )
    evaluation_transform = build_transforms(image_size)
    validation_dataset = CellDataset(validation_records, label_to_index, evaluation_transform)
    test_dataset = CellDataset(test_records, label_to_index, evaluation_transform)
    batch_size = int(training_config["batch_size"])
    workers = int(training_config.get("num_workers", 0))
    train_loader = make_loader(train_dataset, batch_size, workers, shuffle=True, device=device)
    validation_loader = make_loader(
        validation_dataset, batch_size, workers, shuffle=False, device=device
    )

    model = create_model(
        num_classes=len(label_names),
        pretrained=bool(model_config.get("pretrained", False)) and not evaluate_only,
    ).to(device)
    freeze_backbone_epochs = int(model_config.get("freeze_backbone_epochs", 0))
    if freeze_backbone_epochs > 0:
        for parameter in model.features.parameters():
            parameter.requires_grad = False
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(training_config["learning_rate"]),
        weight_decay=float(training_config["weight_decay"]),
    )
    train_label_counts = np.bincount(
        [label_to_index[record.label] for record in train_records],
        minlength=len(label_names),
    )
    if np.any(train_label_counts == 0):
        raise ValueError("Both classes must be present in the training partition.")
    class_weights = train_label_counts.sum() / (
        max(len(label_names), 1) * np.maximum(train_label_counts, 1)
    )
    loss_function = nn.CrossEntropyLoss(
        weight=torch.tensor(class_weights, dtype=torch.float32, device=device)
    )
    output_dir = (root / training_config["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    best_validation_loss = float("inf")
    epochs = 0 if evaluate_only else int(training_config["epochs"])
    log_every = max(1, int(training_config.get("log_every_batches", 20)))
    if not evaluate_only:
        (output_dir / "run-config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    print(
        json.dumps(
            {
                "stage": "ready",
                "device": str(device),
                "workers": workers,
                "batch_size": batch_size,
                "train_images": len(train_records),
                "validation_images": len(validation_records),
                "setup_seconds": round(time.perf_counter() - started, 2),
            }
        ),
        flush=True,
    )

    for epoch in range(1, epochs + 1):
        synchronize(device)
        epoch_started = time.perf_counter()
        if epoch == freeze_backbone_epochs + 1:
            for parameter in model.features.parameters():
                parameter.requires_grad = True
        model.train()
        if epoch <= freeze_backbone_epochs:
            model.features.eval()
        for batch_index, (images, labels) in enumerate(train_loader, start=1):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(images), labels)
            loss.backward()
            optimizer.step()
            if batch_index % log_every == 0 or batch_index == len(train_loader):
                synchronize(device)
                elapsed = time.perf_counter() - epoch_started
                print(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "batch": batch_index,
                            "batches": len(train_loader),
                            "loss": float(loss.detach()),
                            "train_seconds": round(elapsed, 2),
                            "train_eta_seconds": round(
                                elapsed / batch_index * (len(train_loader) - batch_index), 1
                            ),
                        }
                    ),
                    flush=True,
                )
        validation_metrics = evaluate_loader(
            model, validation_loader, device, loss_function, positive_index
        )
        synchronize(device)
        epoch_seconds = time.perf_counter() - epoch_started
        epoch_result = {
            "epoch": epoch,
            "epoch_seconds": round(epoch_seconds, 2),
            "validation_metrics": validation_metrics,
        }
        with (output_dir / "history.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(epoch_result) + "\n")
        print(
            json.dumps(
                {
                    "epoch": epoch,
                    "epoch_seconds": round(epoch_seconds, 2),
                    "validation_loss": validation_metrics["mean_loss"],
                    "validation_weighted_f1": validation_metrics["weighted_f1"],
                }
            )
        )
        if float(validation_metrics["mean_loss"]) < best_validation_loss:
            best_validation_loss = float(validation_metrics["mean_loss"])
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "model_version": model_config.get("version", "hemoscope-mobilenetv3-small-v0"),
                    "label_names": label_names,
                    "positive_label": model_config["positive_label"],
                    "preprocessing": PreprocessingMetadata(image_size=image_size).to_dict(),
                    "seed": seed,
                    "split_manifest_sha256": split_manifest_sha256,
                    "split_provenance": split_provenance,
                    "subject_split_counts": {
                        "train_images": len(train_records),
                        "validation_images": len(validation_records),
                        "test_images": len(test_records),
                        "train_subjects": len({item.subject_id for item in train_records}),
                        "validation_subjects": len(
                            {item.subject_id for item in validation_records}
                        ),
                        "test_subjects": len({item.subject_id for item in test_records}),
                    },
                },
                best_checkpoint,
            )

    checkpoint = torch.load(best_checkpoint, map_location="cpu", weights_only=True)
    if checkpoint["split_manifest_sha256"] != split_manifest_sha256:
        raise ValueError("Current data split does not match the saved checkpoint.")
    if checkpoint["label_names"] != label_names:
        raise ValueError("Current labels do not match the saved checkpoint.")
    if checkpoint["positive_label"] != model_config["positive_label"]:
        raise ValueError("Current positive class does not match the saved checkpoint.")
    if dataset_config.get("frozen_split") is not None:
        if checkpoint.get("split_provenance") != split_provenance:
            raise ValueError("Current grouping provenance does not match the saved checkpoint.")
    if checkpoint["preprocessing"] != PreprocessingMetadata(image_size=image_size).to_dict():
        raise ValueError("Current preprocessing does not match the saved checkpoint.")
    model.load_state_dict(checkpoint["state_dict"])
    test_metrics = None
    if evaluate_only:
        test_loader = make_loader(test_dataset, batch_size, workers, shuffle=False, device=device)
        test_metrics = evaluate_loader(model, test_loader, device, loss_function, positive_index)
        metrics_path = output_dir / "test-metrics.json"
        metrics_path.write_text(json.dumps(test_metrics, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(best_checkpoint.read_bytes()).hexdigest()
    metadata = {
        "model_version": checkpoint["model_version"],
        "checkpoint_sha256": digest,
        "preprocessing": checkpoint["preprocessing"],
        "seed": seed,
        "split_manifest_sha256": split_manifest_sha256,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "subject_split_counts": checkpoint["subject_split_counts"],
        "test_metrics": test_metrics,
        "device": str(device),
        "test_evaluated": evaluate_only,
        "config": config,
        "split_provenance": split_provenance,
        "note": "Research metrics only; not clinical performance evidence.",
    }
    (output_dir / "model-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a subject-split research baseline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/baseline.yaml"),
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Evaluate the saved best checkpoint on the held-out test set without training.",
    )
    parser.add_argument(
        "--check-data-only",
        action="store_true",
        help="Verify dataset and saved assignments without creating or training a model.",
    )
    arguments = parser.parse_args()
    run_training(
        arguments.config,
        evaluate_only=arguments.evaluate_only,
        check_data_only=arguments.check_data_only,
    )


if __name__ == "__main__":
    main()
