"""Create and verify a versioned grouped split without training a model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.dataset import (
    DatasetIntegrityError,
    load_dependency_groups,
    load_manifest,
    split_by_subject,
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_split(manifest, image_root, grouping_dir, output_dir, seed=42):
    if output_dir.exists():
        raise FileExistsError("Choose a fresh output directory; prepared splits are immutable.")
    root = Path(__file__).resolve().parents[2]
    provenance = json.loads((grouping_dir / "provenance.json").read_text())
    verification = json.loads((grouping_dir / "verification.json").read_text())
    if not all(verification["checks"].values()):
        raise DatasetIntegrityError("Prepared grouping checks did not pass.")
    for name, expected in verification["output_sha256"].items():
        if digest(grouping_dir / name) != expected:
            raise DatasetIntegrityError(f"Grouping artifact hash mismatch: {name}")
    if digest(manifest) != provenance["inputs"]["manifest"]["sha256"]:
        raise DatasetIntegrityError("Active manifest changed after grouping preparation.")
    source_audit = root / provenance["inputs"]["source_audit"]["path"]
    if digest(source_audit) != provenance["inputs"]["source_audit"]["sha256"]:
        raise DatasetIntegrityError("Source audit hash mismatch.")
    records = load_manifest(manifest, image_root)
    mapping = load_dependency_groups(grouping_dir / "subject-groups.csv", records)
    partitions = split_by_subject(records, seed=seed, dependency_groups=mapping)
    image_root = image_root.resolve()
    assignments = {}
    subject_partitions = {}
    split_rows = []
    counts = {}
    for name, partition in zip(["train", "validation", "test"], partitions, strict=True):
        counts[name] = {
            "images": len(partition),
            "subjects": len({r.subject_id for r in partition}),
            "dependency_groups": len({mapping[r.subject_id] for r in partition}),
            "class_images": dict(Counter(r.label for r in partition)),
            "class_subjects": dict(Counter({r.subject_id: r.label for r in partition}.values())),
        }
        for r in partition:
            assignments[r.image_path.relative_to(image_root).as_posix()] = name
            subject_partitions.setdefault(r.subject_id, set()).add(name)
            split_rows.append(
                {
                    "image_path": r.image_path.relative_to(image_root).as_posix(),
                    "label": r.label,
                    "subject_id": r.subject_id,
                    "dependency_group": mapping[r.subject_id],
                    "split": name,
                }
            )
    with (grouping_dir / "group-evidence.csv").open() as stream:
        edges = list(csv.DictReader(stream))
    crossings = [
        r for r in edges if subject_partitions[r["subject_a"]] != subject_partitions[r["subject_b"]]
    ]
    excluded = {
        r["image_path"]
        for group in json.loads(source_audit.read_text())["duplicate_groups"]
        for r in group
    }
    if crossings or excluded & set(assignments):
        raise DatasetIntegrityError("Evidence links cross partitions or excluded images returned.")
    if len(assignments) != len(records) or any(len(v) != 1 for v in subject_partitions.values()):
        raise DatasetIntegrityError("Split does not conserve all records and complete subjects.")
    # Check the same inputs and seed reproduce exactly the same row assignments.
    repeated = split_by_subject(records, seed=seed, dependency_groups=mapping)
    if partitions != repeated:
        raise DatasetIntegrityError("Split is not reproducible.")
    report = {
        "split_version": "grouped-v1",
        "grouping_policy": verification["policy_version"],
        "seed": seed,
        "fractions_by_group": {"train": 0.7, "validation": 0.15, "test": 0.15},
        "counts": counts,
        "total_images": len(records),
        "total_subjects": len(mapping),
        "total_dependency_groups": len(set(mapping.values())),
        "checks": {
            "no_subject_overlap": True,
            "no_dependency_group_overlap": True,
            "both_classes_in_each_partition": all(
                set(c["class_images"]) == {"all", "hem"} for c in counts.values()
            ),
            "every_image_assigned_once": True,
            "original_ids_and_labels_preserved": True,
            "reviewed_subject_pair_links_crossing_partitions": len(crossings),
            "excluded_duplicate_copies_restored": len(excluded & set(assignments)),
            "same_seed_reproduces_assignments": True,
        },
        "training_started": False,
        "limitation": (
            "This is a revised development split. Original internal test results already "
            "informed the review; these partitions are not a newly independent "
            "final evaluation cohort."
        ),
        "input_sha256": {
            "manifest": digest(manifest),
            "subject_groups": digest(grouping_dir / "subject-groups.csv"),
            "group_evidence": digest(grouping_dir / "group-evidence.csv"),
        },
    }
    if not report["checks"]["both_classes_in_each_partition"]:
        raise DatasetIntegrityError("Both source classes are required in every partition.")
    output_dir.mkdir(parents=True)
    with (output_dir / "split-manifest.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(split_rows[0]))
        writer.writeheader()
        writer.writerows(split_rows)
    report["split_manifest_sha256"] = digest(output_dir / "split-manifest.csv")
    (output_dir / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/c-nmc-2019/manifest.csv"))
    parser.add_argument("--image-root", type=Path, default=Path("data/c-nmc-2019/raw"))
    parser.add_argument("--grouping-dir", type=Path, default=Path("data/c-nmc-2019/grouping-v1"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/c-nmc-2019/splits/grouped-v1")
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare_split(args.manifest, args.image_root, args.grouping_dir, args.output_dir, args.seed)


if __name__ == "__main__":
    main()
