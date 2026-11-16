import csv
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image
from src.dataset import DatasetIntegrityError, load_manifest
from src.prepare_split import prepare_split
from src.split_config import resolve_split, sha256


@pytest.fixture
def frozen(tmp_path):
    image_root = tmp_path / "images"
    image_root.mkdir()
    manifest = tmp_path / "manifest.csv"
    rows = []
    for i in range(20):
        name = f"{i}.png"
        Image.new("RGB", (32, 32), (i * 10, 80, 120)).save(image_root / name)
        rows.append({"image_path": name, "label": "all" if i % 2 else "hem", "subject_id": f"s{i}"})

    def write(path, data):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)

    write(manifest, rows)
    grouping = tmp_path / "grouping"
    grouping.mkdir()
    write(
        grouping / "subject-groups.csv",
        [
            {
                "subject_id": r["subject_id"],
                "dependency_group": f"g{i // 2}",
                "label": r["label"],
                "retained_image_count": 1,
            }
            for i, r in enumerate(rows)
        ],
    )
    write(
        grouping / "group-evidence.csv",
        [{"subject_a": f"s{i}", "subject_b": f"s{i + 1}"} for i in range(0, 20, 2)],
    )
    policy = {
        "policy_version": "test-v1",
        "checks": {"passed": True},
        "output_sha256": {
            name: sha256(grouping / name) for name in ["subject-groups.csv", "group-evidence.csv"]
        },
    }
    (grouping / "verification.json").write_text(json.dumps(policy))
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"duplicate_groups": []}))
    (grouping / "provenance.json").write_text(
        json.dumps(
            {
                "inputs": {
                    "manifest": {"sha256": sha256(manifest)},
                    "source_audit": {"path": str(audit), "sha256": sha256(audit)},
                }
            }
        )
    )
    output = tmp_path / "split"
    prepare_split(manifest, image_root, grouping, output)
    config = {
        "manifest": str(manifest),
        "image_root": str(image_root),
        "frozen_split": {
            "path": str(output / "split-manifest.csv"),
            "sha256": sha256(output / "split-manifest.csv"),
            "verification_path": str(output / "verification.json"),
            "verification_sha256": sha256(output / "verification.json"),
            "grouping_dir": str(grouping),
            "grouping_verification_sha256": sha256(grouping / "verification.json"),
            "policy_version": "test-v1",
        },
    }
    return tmp_path, config, load_manifest(manifest, image_root)


def test_frozen_assignments_are_not_reshuffled(frozen, monkeypatch):
    root, config, records = frozen

    def fail(*args, **kwargs):
        raise AssertionError("Frozen input must not reshuffle")

    monkeypatch.setattr("src.split_config.split_by_subject", fail)
    parts, content, provenance, snapshots = resolve_split(records, config, root, 42)
    assert content == Path(config["frozen_split"]["path"]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == config["frozen_split"]["sha256"]
    assert sum(len(p) for p in parts) == 20
    assert provenance["mode"] == "frozen_dependency_groups"
    assert len(snapshots) == 4


@pytest.mark.parametrize("target", ["path", "verification_path", "grouping"])
def test_changed_pinned_input_fails(frozen, target):
    root, config, records = frozen
    frozen_config = config["frozen_split"]
    path = (
        Path(frozen_config["grouping_dir"]) / "subject-groups.csv"
        if target == "grouping"
        else Path(frozen_config[target])
    )
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(DatasetIntegrityError, match="hash|changed|differ"):
        resolve_split(records, config, root, 42)


def test_missing_frozen_setting_or_changed_seed_fails(frozen):
    root, config, records = frozen
    with pytest.raises(DatasetIntegrityError, match="seed"):
        resolve_split(records, config, root, 123)
    config["frozen_split"].pop("sha256")
    with pytest.raises(DatasetIntegrityError, match="incomplete"):
        resolve_split(records, config, root, 42)


def test_data_only_preflight_never_creates_model_or_run_folder(frozen, monkeypatch):
    pytest.importorskip("torch")
    import yaml
    from src import train

    root, dataset, _ = frozen
    output = root / "run"
    config = {
        "dataset": dataset,
        "training": {"seed": 42, "output_dir": str(output), "device": "mps"},
        "model": {},
    }
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(config))

    def fail(*args, **kwargs):
        raise AssertionError("Data check must not create a model or select GPU")

    monkeypatch.setattr(train, "create_model", fail)
    monkeypatch.setattr(train, "select_device", fail)
    result = train.run_training(path, check_data_only=True)
    assert result["model_created"] is result["training_started"] is False
    assert not output.exists()


@pytest.mark.parametrize("change", ["missing_image", "changed_label", "cross_partition_group"])
def test_invalid_assignments_fail_even_with_updated_hashes(frozen, change):
    root, config, records = frozen
    path = Path(config["frozen_split"]["path"])
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if change == "missing_image":
        rows.pop()
    elif change == "changed_label":
        rows[0]["label"] = "hem" if rows[0]["label"] == "all" else "all"
    else:
        rows[0]["split"] = "test" if rows[0]["split"] != "test" else "train"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    frozen_config = config["frozen_split"]
    frozen_config["sha256"] = sha256(path)
    report_path = Path(frozen_config["verification_path"])
    report = json.loads(report_path.read_text())
    report["split_manifest_sha256"] = sha256(path)
    report_path.write_text(json.dumps(report))
    frozen_config["verification_sha256"] = sha256(report_path)
    with pytest.raises(DatasetIntegrityError):
        resolve_split(records, config, root, 42)


def test_frozen_checkpoint_keeps_provenance_and_exact_split(frozen):
    torch = pytest.importorskip("torch")
    import yaml
    from src.train import run_training

    torch.set_num_threads(1)
    root, dataset, _ = frozen
    output = root / "trained-fixture"
    config = {
        "dataset": dataset,
        "model": {
            "image_size": 32,
            "pretrained": False,
            "positive_label": "all",
            "freeze_backbone_epochs": 1,
            "version": "test-grouped-v1",
        },
        "training": {
            "seed": 42,
            "output_dir": str(output),
            "device": "cpu",
            "epochs": 1,
            "batch_size": 4,
            "num_workers": 0,
            "learning_rate": 0.0003,
            "weight_decay": 0.0001,
        },
    }
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    run_training(path)
    assert (output / "split-manifest.csv").read_bytes() == Path(
        dataset["frozen_split"]["path"]
    ).read_bytes()
    checkpoint = torch.load(output / "best-checkpoint.pt", map_location="cpu", weights_only=True)
    assert checkpoint["model_version"] == "test-grouped-v1"
    assert checkpoint["split_provenance"]["mode"] == "frozen_dependency_groups"
    assert (output / "grouping-subject-groups.csv").is_file()
    assert not (output / "test-metrics.json").exists()
    run_training(path, evaluate_only=True)
    assert json.loads((output / "model-metadata.json").read_text())["test_evaluated"] is True
