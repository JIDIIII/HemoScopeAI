"""Inspect a saved baseline on its original validation partition, without training."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import torch
import yaml
from PIL import Image, ImageDraw, ImageOps
from torch import nn

from src.dataset import DatasetRecord
from src.inference import CellClassifier
from src.preprocessing import PreprocessingMetadata, build_transforms
from src.train import CellDataset, evaluate_loader, make_loader, select_device


def summarize_subjects(predictions):
    groups = defaultdict(list)
    for row in predictions:
        groups[row["subject_id"]].append(row)
    result = []
    for subject, rows in sorted(groups.items()):
        tp = sum(r["actual_label"] == "all" and r["predicted_label"] == "all" for r in rows)
        fn = sum(r["actual_label"] == "all" and r["predicted_label"] == "hem" for r in rows)
        fp = sum(r["actual_label"] == "hem" and r["predicted_label"] == "all" for r in rows)
        tn = sum(r["actual_label"] == "hem" and r["predicted_label"] == "hem" for r in rows)
        result.append(
            {
                "subject_id": subject,
                "image_count": len(rows),
                "all_count": tp + fn,
                "hem_count": tn + fp,
                "true_positive": tp,
                "false_negative": fn,
                "false_positive": fp,
                "true_negative": tn,
                "error_rate": (fp + fn) / len(rows),
                "sensitivity": tp / (tp + fn) if tp + fn else None,
                "specificity": tn / (tn + fp) if tn + fp else None,
            }
        )
    return result


def write_csv(path, rows):
    if not rows:
        return
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def diagnose(run_dir: Path, output: Path, device_name: str, reference: Path | None = None):
    root = Path(__file__).resolve().parents[1]
    run_dir, output = run_dir.resolve(), output.resolve()
    if output == run_dir or output.is_relative_to(run_dir):
        raise ValueError("Choose an output folder outside the preserved baseline.")
    if output.exists():
        raise FileExistsError("Choose a fresh diagnostic output folder.")
    checkpoint_path = run_dir / "best-checkpoint.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    config = yaml.safe_load((run_dir / "run-config.yaml").read_text())
    split_path = run_dir / "split-manifest.csv"
    digest = hashlib.sha256(split_path.read_bytes()).hexdigest()
    if digest != checkpoint["split_manifest_sha256"]:
        raise ValueError("Saved split hash does not match checkpoint.")
    labels = checkpoint["label_names"]
    if set(labels) != {"all", "hem"} or checkpoint["positive_label"] != "all":
        raise ValueError("Expected ALL-positive binary label mapping.")
    size = checkpoint["preprocessing"]["image_size"]
    if checkpoint["preprocessing"] != PreprocessingMetadata(image_size=size).to_dict():
        raise ValueError("Current preprocessing differs from checkpoint metadata.")
    image_root = (root / config["dataset"]["image_root"]).resolve()
    with split_path.open() as stream:
        rows = list(csv.DictReader(stream))
    validation = []
    subjects = defaultdict(set)
    for row in rows:
        subjects[row["split"]].add(row["subject_id"])
        if row["split"] == "validation":
            path = (image_root / row["image_path"]).resolve()
            if not path.is_relative_to(image_root):
                raise ValueError("Image resolves outside image root.")
            validation.append(DatasetRecord(path, row["label"], row["subject_id"]))
    if not validation:
        raise ValueError("No validation images.")
    if any(
        subjects[a] & subjects[b]
        for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]
    ):
        raise ValueError("Saved split has overlapping subject IDs.")
    device = select_device(device_name)
    classifier = CellClassifier(checkpoint_path, device=str(device))
    label_index = {label: i for i, label in enumerate(labels)}
    dataset = CellDataset(validation, label_index, build_transforms(size))
    loader = make_loader(dataset, 32, 0, shuffle=False, device=device)
    counts = Counter(row["label"] for row in rows if row["split"] == "train")
    weights = [sum(counts.values()) / (2 * counts[label]) for label in labels]
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, device=device))
    metrics = evaluate_loader(classifier.model, loader, device, criterion, label_index["all"])
    history = [json.loads(line) for line in (run_dir / "history.jsonl").read_text().splitlines()]
    best = min(history, key=lambda r: r["validation_metrics"]["mean_loss"])
    f1_delta = abs(metrics["weighted_f1"] - best["validation_metrics"]["weighted_f1"])
    predictions = []
    offset = 0
    with torch.inference_mode():
        for images, _ in loader:
            scores = classifier.model(images.to(device)).softmax(dim=1).cpu()
            for score, record in zip(
                scores, validation[offset : offset + len(scores)], strict=True
            ):
                index = int(score.argmax())
                predictions.append(
                    {
                        "image_path": record.image_path.relative_to(image_root).as_posix(),
                        "subject_id": record.subject_id,
                        "actual_label": record.label,
                        "predicted_label": labels[index],
                        "all_score": float(score[label_index["all"]]),
                        "predicted_class_score": float(score[index]),
                    }
                )
            offset += len(scores)
    # Exercise the public wrapper on up to 32 evenly spaced images across the saved split.
    indices = (
        sorted(
            {
                i * (len(validation) - 1) // min(31, len(validation) - 1)
                for i in range(min(32, len(validation)))
            }
        )
        if len(validation) > 1
        else [0]
    )
    mismatches, differences, all_differences, transforms_equal = [], [], [], True
    for index in indices:
        record = validation[index]
        result = classifier.predict(record.image_path)
        expected = predictions[index]
        with Image.open(record.image_path) as source:
            rgb = source.convert("RGB")
            transforms_equal &= torch.equal(classifier.transform(rgb), dataset.transform(rgb))
        if result.model_label != expected["predicted_label"]:
            mismatches.append(expected["image_path"])
        differences.append(abs(result.raw_model_score - expected["predicted_class_score"]))
        all_differences.append(abs(result.all_score - expected["all_score"]))
    report = {
        "device": str(device),
        "partition": "validation",
        "test_images_evaluated": 0,
        "checkpoint_sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        "split_sha256": digest,
        "label_mapping": label_index,
        "expected_best_epoch": best["epoch"],
        "metrics": metrics,
        "expected_validation_metrics": best["validation_metrics"],
        "weighted_f1_absolute_difference": f1_delta,
        "validation_reproduced_within_0_001": f1_delta <= 0.001,
        "wrapper_sample_count": len(indices),
        "wrapper_label_mismatches": mismatches,
        "wrapper_max_score_difference": max(differences),
        "wrapper_max_all_score_difference": max(all_differences),
        "sample_preprocessing_equal": transforms_equal,
        "score_note": "ALL score is softmax output, not a calibrated probability.",
    }
    if reference is not None:
        reference_summary = json.loads((reference / "summary.json").read_text())
        if reference_summary["checkpoint_sha256"] != report["checkpoint_sha256"]:
            raise ValueError("Reference uses a different checkpoint.")
        if reference_summary["split_sha256"] != digest:
            raise ValueError("Reference uses a different split.")
        with (reference / "predictions.csv").open() as stream:
            previous = {row["image_path"]: row for row in csv.DictReader(stream)}
        if set(previous) != {row["image_path"] for row in predictions}:
            raise ValueError("Reference validation image lists differ.")
        report["reference_comparison"] = {
            "reference_device": reference_summary["device"],
            "image_count": len(predictions),
            "label_disagreements": sum(
                row["predicted_label"] != previous[row["image_path"]]["predicted_label"]
                for row in predictions
            ),
            "max_all_score_difference": max(
                abs(row["all_score"] - float(previous[row["image_path"]]["all_score"]))
                for row in predictions
            ),
        }
    output.mkdir(parents=True)
    write_csv(output / "predictions.csv", predictions)
    write_csv(output / "subjects.csv", summarize_subjects(predictions))
    mistakes = [r for r in predictions if r["actual_label"] != r["predicted_label"]]
    examples = []
    for actual in ["hem", "all"]:
        candidates = [r for r in mistakes if r["actual_label"] == actual]
        examples.extend(
            sorted(candidates, key=lambda r: r["predicted_class_score"], reverse=True)[:8]
        )
    if examples:
        sheet = Image.new("RGB", (4 * 230, ((len(examples) + 3) // 4) * 260), "white")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(examples):
            x, y = (index % 4) * 230, (index // 4) * 260
            with Image.open(image_root / row["image_path"]) as image:
                sheet.paste(ImageOps.contain(image.convert("RGB"), (220, 200)), (x, y))
            draw.text(
                (x, y + 202),
                f"{row['subject_id']}\n{row['actual_label']} -> {row['predicted_label']}\n"
                f"ALL score: {row['all_score']:.4f}",
                fill="black",
            )
        sheet.save(output / "mistakes.jpg")
        write_csv(output / "mistake-examples.csv", examples)
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "mps", "auto"], default="mps")
    parser.add_argument(
        "--reference", type=Path, help="Compare predictions with an earlier diagnostic folder."
    )
    args = parser.parse_args()
    diagnose(args.run, args.output, args.device, args.reference)


if __name__ == "__main__":
    main()
