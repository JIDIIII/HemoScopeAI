import csv

from PIL import Image
from src.dataset import DatasetIntegrityError, load_manifest, split_by_subject


def make_manifest(tmp_path, rows):
    root = tmp_path / "images"
    root.mkdir()
    for index, row in enumerate(rows):
        Image.new("RGB", (12, 12), (120, 80, index % 256)).save(root / row["image_path"])
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image_path", "label", "subject_id"])
        writer.writeheader()
        writer.writerows(rows)
    return manifest, root


def test_load_manifest_rejects_duplicate_paths(tmp_path):
    rows = [
        {"image_path": "a.png", "label": "all", "subject_id": "subject-1"},
        {"image_path": "a.png", "label": "all", "subject_id": "subject-1"},
    ]
    manifest, root = make_manifest(tmp_path, rows)
    try:
        load_manifest(manifest, root)
    except DatasetIntegrityError as error:
        assert "Duplicate" in str(error)
    else:
        raise AssertionError("Duplicate image paths must be rejected.")


def test_load_manifest_rejects_duplicate_image_content(tmp_path):
    root = tmp_path / "images"
    root.mkdir()
    first = root / "a.png"
    second = root / "b.png"
    Image.new("RGB", (12, 12), (120, 80, 60)).save(first)
    second.write_bytes(first.read_bytes())
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image_path", "label", "subject_id"])
        writer.writeheader()
        writer.writerows(
            [
                {"image_path": "a.png", "label": "all", "subject_id": "subject-1"},
                {"image_path": "b.png", "label": "all", "subject_id": "subject-2"},
            ]
        )
    try:
        load_manifest(manifest, root)
    except DatasetIntegrityError as error:
        assert "Duplicate image content" in str(error)
    else:
        raise AssertionError("Duplicate image content must be rejected.")


def test_subject_split_has_no_subject_leakage(tmp_path):
    rows = [
        {
            "image_path": f"image-{subject}-{index}.png",
            "label": "all" if subject % 2 else "hem",
            "subject_id": f"subject-{subject}",
        }
        for subject in range(20)
        for index in range(2)
    ]
    manifest, root = make_manifest(tmp_path, rows)
    records = load_manifest(manifest, root)
    train, validation, test = split_by_subject(records, seed=27)
    subject_sets = [
        {record.subject_id for record in partition} for partition in (train, validation, test)
    ]
    assert not (subject_sets[0] & subject_sets[1])
    assert not (subject_sets[0] & subject_sets[2])
    assert not (subject_sets[1] & subject_sets[2])
