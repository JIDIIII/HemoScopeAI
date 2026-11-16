import csv
import json

import pytest
import yaml
from PIL import Image

torch = pytest.importorskip("torch")
training = pytest.importorskip("src.train")
run_training = training.run_training
select_device = training.select_device


def test_device_selection_and_unavailable_device(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    assert select_device().type == "mps"
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    assert select_device().type == "cpu"
    with pytest.raises(ValueError, match="unavailable"):
        select_device("mps")


@pytest.mark.parametrize("device", ["cpu", "mps"])
def test_training_keeps_test_separate_and_refuses_overwrite(tmp_path, device):
    if device == "mps" and not torch.backends.mps.is_available():
        pytest.skip("MPS GPU unavailable in this environment")
    torch.set_num_threads(1)
    images = tmp_path / "images"
    images.mkdir()
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["image_path", "label", "subject_id"])
        for index in range(40):
            name = f"{index}.png"
            Image.new("RGB", (32, 32), (index * 5, 80, 120)).save(images / name)
            writer.writerow([name, "all" if (index // 2) % 2 else "hem", str(index // 2)])
    output = tmp_path / "run"
    config = {
        "dataset": {
            "manifest": str(manifest),
            "image_root": str(images),
            "train_fraction": 0.7,
            "validation_fraction": 0.15,
            "test_fraction": 0.15,
        },
        "model": {
            "image_size": 32,
            "pretrained": False,
            "positive_label": "all",
            "freeze_backbone_epochs": 1,
        },
        "training": {
            "seed": 42,
            "epochs": 1,
            "batch_size": 4,
            "num_workers": 0,
            "device": device,
            "learning_rate": 0.0003,
            "weight_decay": 0.0001,
            "output_dir": str(output),
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    run_training(path)
    assert (output / "best-checkpoint.pt").is_file()
    assert not (output / "test-metrics.json").exists()
    assert json.loads((output / "model-metadata.json").read_text())["test_evaluated"] is False
    with pytest.raises(FileExistsError):
        run_training(path)
    run_training(path, evaluate_only=True)
    assert json.loads((output / "test-metrics.json").read_text())["sample_count"] > 0
    from src.diagnose import diagnose

    baseline_bytes = {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()}
    diagnostic = tmp_path / "diagnostic"
    diagnose(output, diagnostic, device)
    summary = json.loads((diagnostic / "summary.json").read_text())
    assert summary["validation_reproduced_within_0_001"] is True
    assert summary["wrapper_label_mismatches"] == []
    assert summary["sample_preprocessing_equal"] is True
    assert summary["test_images_evaluated"] == 0
    assert (diagnostic / "predictions.csv").is_file()
    assert (diagnostic / "subjects.csv").is_file()
    assert {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()} == baseline_bytes
    with pytest.raises(ValueError, match="outside"):
        diagnose(output, output / "nested", device)
    split_bytes = (output / "split-manifest.csv").read_bytes()
    config["training"]["seed"] = 123
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="split"):
        run_training(path, evaluate_only=True)
    assert (output / "split-manifest.csv").read_bytes() == split_bytes
