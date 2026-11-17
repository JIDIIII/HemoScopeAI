"""Prepare BCCD VOC annotations and preserve its supplied image-level split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

SPLITS = ("train", "val", "test")
IMAGE_FIELDS = (
    "image_id",
    "image_path",
    "split",
    "width",
    "height",
    "box_count",
)
ANNOTATION_FIELDS = (
    "image_id",
    "split",
    "object_index",
    "class_name",
    "voc_xmin",
    "voc_ymin",
    "voc_xmax",
    "voc_ymax",
    "difficult",
    "truncated",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_image_ids(path: Path) -> list[str]:
    ids = [Path(line.strip()).stem for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [image_id for image_id in ids if image_id]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate image IDs in split file: {path}")
    return ids


def read_box_value(box: ET.Element, name: str, *, image_id: str) -> float:
    value = box.findtext(name)
    if value is None:
        raise ValueError(f"Missing {name} in annotation for {image_id}")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {name}={value!r} in annotation for {image_id}") from exc


def format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path.home() / "Downloads" / "DATASETS" / "BCCD",
        help="Local BCCD repository root (contains BCCD/Annotations and BCCD/JPEGImages).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "bccd-detector-v1",
        help="Directory for generated CSV and JSON manifests; ignored by Git.",
    )
    args = parser.parse_args()

    dataset_root = args.dataset_root.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    annotation_dir = dataset_root / "BCCD" / "Annotations"
    image_dir = dataset_root / "BCCD" / "JPEGImages"
    split_dir = dataset_root / "BCCD" / "ImageSets" / "Main"

    for required in (annotation_dir, image_dir, split_dir):
        if not required.is_dir():
            raise FileNotFoundError(f"Expected BCCD directory does not exist: {required}")

    xml_files = sorted(annotation_dir.glob("*.xml"), key=lambda path: path.stem)
    image_files = sorted(
        (path for path in image_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg"}),
        key=lambda path: path.stem,
    )
    xml_by_id = {path.stem: path for path in xml_files}
    image_by_id = {path.stem: path for path in image_files}
    if len(xml_by_id) != len(xml_files) or len(image_by_id) != len(image_files):
        raise ValueError("Duplicate image IDs found in BCCD annotation or image filenames.")
    if set(xml_by_id) != set(image_by_id):
        raise ValueError(
            "BCCD image and XML IDs differ: "
            f"missing_images={sorted(set(xml_by_id) - set(image_by_id))[:5]}, "
            f"missing_annotations={sorted(set(image_by_id) - set(xml_by_id))[:5]}"
        )

    split_ids = {
        split: load_image_ids(split_dir / f"{split}.txt")
        for split in SPLITS
    }
    split_sets = {split: set(ids) for split, ids in split_ids.items()}
    trainval_path = split_dir / "trainval.txt"
    trainval_ids = set(load_image_ids(trainval_path)) if trainval_path.is_file() else None

    overlaps = {
        f"{left}_{right}": sorted(split_sets[left] & split_sets[right])
        for index, left in enumerate(SPLITS)
        for right in SPLITS[index + 1 :]
    }
    if any(overlaps.values()):
        raise ValueError(f"BCCD source split files overlap: {overlaps}")
    all_split_ids = set.union(*split_sets.values())
    if all_split_ids != set(image_by_id):
        raise ValueError(
            "BCCD split files do not cover the annotated images exactly: "
            f"missing={sorted(set(image_by_id) - all_split_ids)[:5]}, "
            f"unknown={sorted(all_split_ids - set(image_by_id))[:5]}"
        )
    if trainval_ids is not None and trainval_ids != split_sets["train"] | split_sets["val"]:
        raise ValueError("BCCD trainval.txt does not equal the union of train.txt and val.txt.")

    assignment = {image_id: split for split, ids in split_sets.items() for image_id in ids}
    image_rows: list[dict[str, object]] = []
    annotation_rows: list[dict[str, object]] = []
    box_counts: dict[str, Counter[str]] = defaultdict(Counter)
    class_image_ids: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {split: set() for split in SPLITS}
    )
    annotation_digest = hashlib.sha256()

    for image_id in sorted(image_by_id):
        xml_path = xml_by_id[image_id]
        xml_bytes = xml_path.read_bytes()
        annotation_digest.update(xml_path.name.encode("utf-8"))
        annotation_digest.update(b"\0")
        annotation_digest.update(xml_bytes)
        root = ET.fromstring(xml_bytes)
        xml_filename = root.findtext("filename")
        if xml_filename is None or Path(xml_filename).stem != image_id:
            raise ValueError(f"Annotation filename does not match XML name: {xml_path}")

        size = root.find("size")
        if size is None:
            raise ValueError(f"Missing image size in annotation: {xml_path}")
        width = int(size.findtext("width", "0"))
        height = int(size.findtext("height", "0"))
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid image dimensions in annotation: {xml_path}")

        image_path = image_by_id[image_id]
        with Image.open(image_path) as image:
            if image.size != (width, height):
                raise ValueError(
                    f"XML/image dimensions differ for {image_id}: "
                    f"xml={(width, height)}, image={image.size}"
                )

        split = assignment[image_id]
        objects = root.findall("object")
        image_rows.append(
            {
                "image_id": image_id,
                "image_path": image_path.relative_to(dataset_root).as_posix(),
                "split": split,
                "width": width,
                "height": height,
                "box_count": len(objects),
            }
        )

        for object_index, obj in enumerate(objects):
            class_name = (obj.findtext("name") or "").strip()
            if not class_name:
                raise ValueError(f"Missing object class in annotation for {image_id}")
            box = obj.find("bndbox")
            if box is None:
                raise ValueError(f"Missing bounding box for {image_id}, object {object_index}")
            coordinates = {
                key: read_box_value(box, key, image_id=image_id)
                for key in ("xmin", "ymin", "xmax", "ymax")
            }
            x_min, y_min = coordinates["xmin"], coordinates["ymin"]
            x_max, y_max = coordinates["xmax"], coordinates["ymax"]
            if not (1 <= x_min <= x_max <= width and 1 <= y_min <= y_max <= height):
                raise ValueError(
                    f"VOC box out of bounds for {image_id}, object {object_index}: "
                    f"{coordinates}, image={(width, height)}"
                )

            annotation_rows.append(
                {
                    "image_id": image_id,
                    "split": split,
                    "object_index": object_index,
                    "class_name": class_name,
                    "voc_xmin": format_number(x_min),
                    "voc_ymin": format_number(y_min),
                    "voc_xmax": format_number(x_max),
                    "voc_ymax": format_number(y_max),
                    "difficult": (obj.findtext("difficult") or "0").strip(),
                    "truncated": (obj.findtext("truncated") or "0").strip(),
                }
            )
            box_counts[split][class_name] += 1
            class_image_ids[class_name][split].add(image_id)

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite non-empty output directory: {output_dir}. "
            "Choose a new --output-dir to preserve this preparation snapshot."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    images_path = output_dir / "images.csv"
    annotations_path = output_dir / "annotations.csv"
    write_csv(images_path, IMAGE_FIELDS, image_rows)
    write_csv(annotations_path, ANNOTATION_FIELDS, annotation_rows)

    split_summary = {
        split: {
            "images": len(split_sets[split]),
            "boxes": sum(box_counts[split].values()),
            "box_count_by_class": dict(sorted(box_counts[split].items())),
            "images_with_class": {
                name: len(class_image_ids[name][split])
                for name in sorted(class_image_ids)
            },
        }
        for split in SPLITS
    }
    summary = {
        "dataset": "BCCD",
        "dataset_root_recorded": False,
        "image_path_convention": "relative to --dataset-root",
        "source_split_files": {
            f"{split}.txt": sha256_bytes((split_dir / f"{split}.txt").read_bytes())
            for split in SPLITS
        },
        "trainval_matches_train_plus_val": trainval_ids is None
        or trainval_ids == split_sets["train"] | split_sets["val"],
        "split_policy": "provided BCCD train/val/test files; images are the split unit",
        "split_counts": split_summary,
        "total_images": len(image_rows),
        "total_boxes": len(annotation_rows),
        "all_box_counts_by_class": dict(
            sorted(Counter(row["class_name"] for row in annotation_rows).items())
        ),
        "coordinate_convention": "original Pascal VOC values preserved (1-based inclusive)",
        "annotation_xml_sha256": annotation_digest.hexdigest(),
        "images_csv_sha256": sha256_bytes(images_path.read_bytes()),
        "annotations_csv_sha256": sha256_bytes(annotations_path.read_bytes()),
        "validation": {
            "images_and_xml_ids_match": True,
            "each_image_has_one_split": True,
            "splits_are_disjoint": True,
            "split_files_cover_all_annotated_images": True,
            "image_dimensions_match_xml": True,
            "all_boxes_within_image_bounds": True,
            "subject_or_slide_independence_verified": False,
        },
        "note": (
            "Research prototype data only. The source files do not establish patient/slide "
            "independence; do not claim patient-independent detector performance."
        ),
    }
    summary_path = output_dir / "split-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "stage": "bccd_preparation_complete",
                "output_dir": str(output_dir),
                "images": len(image_rows),
                "boxes": len(annotation_rows),
                "splits": split_summary,
                "subject_or_slide_independence_verified": False,
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
