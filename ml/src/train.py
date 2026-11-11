from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
from pathlib import Path

import numpy as np
import torch
import torchvision
import yaml
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.dataset import DatasetRecord, load_manifest, split_by_subject
from src.evaluate import compute_metrics
from src.model import create_model
from src.preprocessing import PreprocessingMetadata, build_transforms


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


def run_training(config_path: Path) -> None:
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    root = Path(__file__).resolve().parents[1]
    dataset_config = config["dataset"]
    training_config = config["training"]
    model_config = config["model"]
    image_root = (root / dataset_config["image_root"]).resolve()
    manifest_path = (root / dataset_config["manifest"]).resolve()
    records = load_manifest(manifest_path, image_root)
    train_records, validation_records, test_records = split_by_subject(
        records,
        train_fraction=float(dataset_config["train_fraction"]),
        validation_fraction=float(dataset_config["validation_fraction"]),
        test_fraction=float(dataset_config["test_fraction"]),
        seed=int(training_config["seed"]),
    )
    split_path = (root / training_config["output_dir"] / "split-manifest.csv").resolve()
    split_path.parent.mkdir(parents=True, exist_ok=True)
    with split_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image_path", "label", "subject_id", "split"])
        writer.writeheader()
        for partition_name, partition in (
            ("train", train_records),
            ("validation", validation_records),
            ("test", test_records),
        ):
            for record in partition:
                writer.writerow(
                    {
                        "image_path": record.image_path.relative_to(image_root),
                        "label": record.label,
                        "subject_id": record.subject_id,
                        "split": partition_name,
                    }
                )
    split_manifest_sha256 = hashlib.sha256(split_path.read_bytes()).hexdigest()

    seed = int(training_config["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=workers
    )
    validation_loader = DataLoader(
        validation_dataset, batch_size=batch_size, shuffle=False, num_workers=workers
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=workers
    )

    model = create_model(
        num_classes=len(label_names),
        pretrained=bool(model_config.get("pretrained", False)),
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
    best_checkpoint = output_dir / "best-checkpoint.pt"
    epochs = int(training_config["epochs"])

    for epoch in range(1, epochs + 1):
        if epoch == freeze_backbone_epochs + 1:
            for parameter in model.features.parameters():
                parameter.requires_grad = True
        model.train()
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(images), labels)
            loss.backward()
            optimizer.step()
        validation_metrics = evaluate_loader(
            model, validation_loader, device, loss_function, positive_index
        )
        print(
            json.dumps(
                {
                    "epoch": epoch,
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
                    "model_version": "hemoscope-mobilenetv3-small-v0",
                    "label_names": label_names,
                    "positive_label": model_config["positive_label"],
                    "preprocessing": PreprocessingMetadata(image_size=image_size).to_dict(),
                    "seed": seed,
                    "split_manifest_sha256": split_manifest_sha256,
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

    checkpoint = torch.load(best_checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["state_dict"])
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
    arguments = parser.parse_args()
    run_training(arguments.config)


if __name__ == "__main__":
    main()
