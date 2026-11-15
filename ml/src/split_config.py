"""Resolve pinned grouped assignments, or preserve the original subject-split workflow."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from src.dataset import DatasetIntegrityError, load_dependency_groups, split_by_subject


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_split(records, dataset_config, root: Path, seed: int):
    frozen = dataset_config.get("frozen_split")
    if frozen is None:
        parts = split_by_subject(
            records,
            train_fraction=float(dataset_config["train_fraction"]),
            validation_fraction=float(dataset_config["validation_fraction"]),
            test_fraction=float(dataset_config["test_fraction"]),
            seed=seed,
        )
        with io.StringIO(newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=["image_path", "label", "subject_id", "split"]
            )
            writer.writeheader()
            image_root = (root / dataset_config["image_root"]).resolve()
            for name, part in zip(["train", "validation", "test"], parts, strict=True):
                for record in part:
                    writer.writerow(
                        {
                            "image_path": record.image_path.relative_to(image_root),
                            "label": record.label,
                            "subject_id": record.subject_id,
                            "split": name,
                        }
                    )
            content = stream.getvalue().encode("utf-8")
        return parts, content, {"mode": "subject_id", "seed": seed}, {}
    # An incomplete frozen configuration must fail, never fall back to random splitting.
    required = {
        "path",
        "sha256",
        "verification_path",
        "verification_sha256",
        "grouping_dir",
        "grouping_verification_sha256",
        "policy_version",
    }
    if not isinstance(frozen, dict) or not required.issubset(frozen):
        raise DatasetIntegrityError("Frozen split configuration is incomplete.")
    path = (root / frozen["path"]).resolve()
    report_path = (root / frozen["verification_path"]).resolve()
    grouping = (root / frozen["grouping_dir"]).resolve()
    grouping_report_path = grouping / "verification.json"
    for source, expected in [
        (path, frozen["sha256"]),
        (report_path, frozen["verification_sha256"]),
        (grouping_report_path, frozen["grouping_verification_sha256"]),
    ]:
        if sha256(source) != expected:
            raise DatasetIntegrityError(f"Pinned artifact hash mismatch: {source.name}")
    report = json.loads(report_path.read_text())
    policy = json.loads(grouping_report_path.read_text())
    if (
        report["seed"] != seed
        or report["grouping_policy"] != frozen["policy_version"]
        or policy["policy_version"] != frozen["policy_version"]
    ):
        raise DatasetIntegrityError("Frozen split seed or policy does not match configuration.")
    if report["split_manifest_sha256"] != frozen["sha256"]:
        raise DatasetIntegrityError("Frozen split verification hash disagrees.")
    if not all(policy["checks"].values()):
        raise DatasetIntegrityError("Prepared grouping verification did not pass.")
    for name, expected in policy["output_sha256"].items():
        if sha256(grouping / name) != expected:
            raise DatasetIntegrityError(f"Grouping input changed: {name}")
    actual_manifest_hash = sha256(root / dataset_config["manifest"])
    if actual_manifest_hash != report["input_sha256"]["manifest"]:
        raise DatasetIntegrityError("Dataset manifest changed after the frozen split was prepared.")
    if (
        sha256(grouping / "subject-groups.csv") != report["input_sha256"]["subject_groups"]
        or sha256(grouping / "group-evidence.csv") != report["input_sha256"]["group_evidence"]
    ):
        raise DatasetIntegrityError("Grouping inputs differ from the frozen split.")
    mapping = load_dependency_groups(grouping / "subject-groups.csv", records)
    image_root = (root / dataset_config["image_root"]).resolve()
    lookup = {r.image_path.resolve(): r for r in records}
    parts = {name: [] for name in ["train", "validation", "test"]}
    seen = set()
    subject_parts = {}
    group_parts = {}
    content = path.read_bytes()
    with io.StringIO(content.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        columns = {"image_path", "label", "subject_id", "dependency_group", "split"}
        if reader.fieldnames is None or not columns.issubset(reader.fieldnames):
            raise DatasetIntegrityError("Frozen split columns are missing.")
        for row in reader:
            image = (image_root / row["image_path"]).resolve()
            record = lookup.get(image)
            if record is None or image in seen or not image.is_relative_to(image_root):
                raise DatasetIntegrityError(
                    "Frozen split has an extra, duplicate or invalid image."
                )
            if (
                row["subject_id"] != record.subject_id
                or row["label"] != record.label
                or row["dependency_group"] != mapping[record.subject_id]
            ):
                raise DatasetIntegrityError("Frozen split changes a source ID, label or group.")
            name = row["split"]
            if name not in parts:
                raise DatasetIntegrityError("Unknown frozen partition.")
            for key, assignment in [
                (record.subject_id, subject_parts),
                (mapping[record.subject_id], group_parts),
            ]:
                if key in assignment and assignment[key] != name:
                    raise DatasetIntegrityError("A subject or dependency group crosses partitions.")
                assignment[key] = name
            seen.add(image)
            parts[name].append(record)
    if seen != set(lookup):
        raise DatasetIntegrityError("Frozen split is missing dataset images.")
    counts = {}
    for name, part in parts.items():
        counts[name] = {
            "images": len(part),
            "subjects": len({r.subject_id for r in part}),
            "dependency_groups": len({mapping[r.subject_id] for r in part}),
            "class_images": dict(Counter(r.label for r in part)),
        }
        if set(counts[name]["class_images"]) != {"all", "hem"}:
            raise DatasetIntegrityError("Both classes must occur in every frozen partition.")
        if any(counts[name][key] != report["counts"][name][key] for key in counts[name]):
            raise DatasetIntegrityError("Frozen split counts differ from verification report.")
    with (grouping / "group-evidence.csv").open() as stream:
        for edge in csv.DictReader(stream):
            if subject_parts[edge["subject_a"]] != subject_parts[edge["subject_b"]]:
                raise DatasetIntegrityError("A reviewed image relationship crosses partitions.")
    provenance = {
        "mode": "frozen_dependency_groups",
        "seed": seed,
        "grouping_policy": frozen["policy_version"],
        "counts": counts,
        "manifest_sha256": actual_manifest_hash,
        "split_manifest_sha256": frozen["sha256"],
        "split_verification_sha256": frozen["verification_sha256"],
        "grouping_verification_sha256": frozen["grouping_verification_sha256"],
        "grouping_artifact_sha256": policy["output_sha256"],
    }
    snapshots = {
        "frozen-split-verification.json": report_path,
        "grouping-verification.json": grouping_report_path,
        "grouping-subject-groups.csv": grouping / "subject-groups.csv",
        "grouping-evidence.csv": grouping / "group-evidence.csv",
    }
    return tuple(parts.values()), content, provenance, snapshots
