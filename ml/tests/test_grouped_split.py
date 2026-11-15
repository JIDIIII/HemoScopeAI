import csv
from pathlib import Path

import pytest

from src.dataset import (
    DatasetIntegrityError,
    DatasetRecord,
    load_dependency_groups,
    split_by_subject,
)


def records():
    return [DatasetRecord(Path(f"{i}.png"), "all" if i % 2 else "hem", f"s{i}") for i in range(30)]


def test_related_subjects_stay_together_and_seed_is_reproducible():
    data = records()
    mapping = {f"s{i}": f"g{i // 2}" for i in range(30)}
    partitions = split_by_subject(data, dependency_groups=mapping, seed=42)
    assert partitions == split_by_subject(data, dependency_groups=mapping, seed=42)
    group_sets = [{mapping[r.subject_id] for r in p} for p in partitions]
    assert not (
        group_sets[0] & group_sets[1]
        or group_sets[0] & group_sets[2]
        or group_sets[1] & group_sets[2]
    )
    assert sum(len(p) for p in partitions) == len(data)
    assert {r for p in partitions for r in p} == set(data)
    assert all({r.label for r in p} == {"all", "hem"} for p in partitions)


@pytest.mark.parametrize("change", ["missing", "extra", "blank"])
def test_bad_group_coverage_fails(change):
    mapping = {f"s{i}": f"g{i // 2}" for i in range(30)}
    if change == "missing":
        mapping.pop("s0")
    elif change == "extra":
        mapping["unknown"] = "g0"
    else:
        mapping["s0"] = ""
    with pytest.raises(DatasetIntegrityError):
        split_by_subject(records(), dependency_groups=mapping)


def test_missing_class_in_partition_fails_without_retry():
    data = [DatasetRecord(Path(f"{i}.png"), "all" if i else "hem", f"s{i}") for i in range(3)]
    with pytest.raises(DatasetIntegrityError, match="all source classes"):
        split_by_subject(data, dependency_groups={f"s{i}": f"g{i}" for i in range(3)})


@pytest.mark.parametrize("change", ["duplicate", "label", "count", "missing", "extra"])
def test_sidecar_disagreement_fails(tmp_path, change):
    data = records()
    rows = [
        {
            "subject_id": r.subject_id,
            "dependency_group": f"g{i // 2}",
            "label": r.label,
            "retained_image_count": 1,
        }
        for i, r in enumerate(data)
    ]
    if change == "duplicate":
        rows.append(rows[0])
    elif change == "label":
        rows[0]["label"] = "all"
    elif change == "count":
        rows[0]["retained_image_count"] = 2
    elif change == "missing":
        rows.pop()
    else:
        rows.append({**rows[0], "subject_id": "unknown"})
    path = tmp_path / "groups.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(DatasetIntegrityError):
        load_dependency_groups(path, data)
