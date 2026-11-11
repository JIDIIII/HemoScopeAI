from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


class DatasetIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetRecord:
    image_path: Path
    label: str
    subject_id: str


def load_manifest(manifest_path: Path, image_root: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    seen_paths: set[Path] = set()
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required_columns = {"image_path", "label", "subject_id"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise DatasetIntegrityError(
                "Manifest must contain image_path, label, and subject_id columns."
            )
        for row_number, row in enumerate(reader, start=2):
            relative_path = Path((row.get("image_path") or "").strip())
            label = (row.get("label") or "").strip()
            subject_id = (row.get("subject_id") or "").strip()
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise DatasetIntegrityError(f"Manifest row {row_number} has an unsafe image path.")
            if not label or not subject_id:
                raise DatasetIntegrityError(
                    f"Manifest row {row_number} is missing a label or subject ID."
                )
            image_path = (image_root / relative_path).resolve()
            if not image_path.is_relative_to(image_root.resolve()):
                raise DatasetIntegrityError(
                    f"Manifest row {row_number} resolves outside the image root."
                )
            if image_path in seen_paths:
                raise DatasetIntegrityError(f"Duplicate image path on manifest row {row_number}.")
            seen_paths.add(image_path)
            if not image_path.is_file():
                raise DatasetIntegrityError(
                    f"Image on manifest row {row_number} does not exist: {relative_path}"
                )
            records.append(
                DatasetRecord(
                    image_path=image_path,
                    label=label,
                    subject_id=subject_id,
                )
            )
    if not records:
        raise DatasetIntegrityError("Manifest contains no image rows.")
    verify_image_integrity(records)
    return records


def verify_integrity(records: list[DatasetRecord]) -> None:
    if not records:
        raise DatasetIntegrityError("No records were provided.")
    paths = [record.image_path for record in records]
    if len(paths) != len(set(paths)):
        raise DatasetIntegrityError("Dataset contains duplicate image paths.")
    if any(not record.subject_id.strip() for record in records):
        raise DatasetIntegrityError("Every record must have a non-empty subject ID.")
    if any(not record.label.strip() for record in records):
        raise DatasetIntegrityError("Every record must have a non-empty label.")


def verify_image_integrity(records: list[DatasetRecord]) -> None:
    """Decode each image and reject duplicate content before a training run."""
    digests: dict[str, Path] = {}
    for record in records:
        try:
            with Image.open(record.image_path) as image:
                if image.width < 1 or image.height < 1:
                    raise DatasetIntegrityError(
                        f"Image has invalid dimensions: {record.image_path}"
                    )
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise DatasetIntegrityError(f"Image could not be decoded: {record.image_path}") from exc
        digest = hashlib.sha256(record.image_path.read_bytes()).hexdigest()
        previous = digests.get(digest)
        if previous is not None:
            raise DatasetIntegrityError(
                f"Duplicate image content found at {previous} and {record.image_path}."
            )
        digests[digest] = record.image_path


def split_by_subject(
    records: list[DatasetRecord],
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    test_fraction: float = 0.15,
    seed: int = 42,
) -> tuple[list[DatasetRecord], list[DatasetRecord], list[DatasetRecord]]:
    """Split complete subjects into partitions using sklearn GroupShuffleSplit."""
    total = train_fraction + validation_fraction + test_fraction
    if any(value <= 0 for value in (train_fraction, validation_fraction, test_fraction)):
        raise ValueError("Every split fraction must be greater than zero.")
    if abs(total - 1.0) > 1e-6:
        raise ValueError("Train, validation, and test fractions must sum to 1.")
    verify_integrity(records)
    if len({record.subject_id for record in records}) < 3:
        raise DatasetIntegrityError("At least three distinct subjects are required for splitting.")

    try:
        import numpy as np
        from sklearn.model_selection import GroupShuffleSplit
    except ImportError as exc:
        raise RuntimeError(
            'Install the ML training dependencies with: python -m pip install -e ".[train]"'
        ) from exc

    indices = np.arange(len(records))
    groups = np.asarray([record.subject_id for record in records])
    test_splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_fraction,
        random_state=seed,
    )
    remaining_indices, test_indices = next(test_splitter.split(indices, groups=groups))

    relative_validation_fraction = validation_fraction / (train_fraction + validation_fraction)
    remaining_groups = groups[remaining_indices]
    validation_splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=relative_validation_fraction,
        random_state=seed + 1,
    )
    train_positions, validation_positions = next(
        validation_splitter.split(remaining_indices, groups=remaining_groups)
    )
    train_indices = remaining_indices[train_positions]
    validation_indices = remaining_indices[validation_positions]

    partitions = (
        [records[int(index)] for index in train_indices],
        [records[int(index)] for index in validation_indices],
        [records[int(index)] for index in test_indices],
    )
    subject_sets = [{record.subject_id for record in partition} for partition in partitions]
    if any(
        subject_sets[left] & subject_sets[right]
        for left in range(3)
        for right in range(left + 1, 3)
    ):
        raise DatasetIntegrityError("A subject appears in more than one dataset partition.")
    return partitions
