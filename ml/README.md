# HemoScope AI ML pipeline

This package scaffolds a reproducible MobileNetV3-Small transfer-learning workflow for selected-cell research images. C-NMC 2019 is the planned initial dataset. No dataset, model checkpoint, clinical metric, or sample prediction is included.

## Install and prepare data

For dataset integrity and subject-split checks only, install `python -m pip install -e "ml/[dev]"`. Training/inference and associated checkpoint tests require the `train` extra and PyTorch, but no test command downloads C-NMC data.

For training, install the additional model dependencies:

~~~sh
python -m pip install -e "ml/[train,dev]"
~~~

Review C-NMC 2019 terms and attribution before obtaining it. Prepare a manifest with image_path,label,subject_id columns and keep all images for one subject in a single train, validation, or test partition. The sample config points to a local manifest but does not download data.

See [the dataset workspace instructions](data/README.md) for the `raw/` layout, local download links, original challenge partitions, and audit/exclusion policy. The baseline config expects `data/c-nmc-2019/manifest.csv` and `data/c-nmc-2019/raw`. A local preparation report records the actual usable count after duplicate exclusions; do not substitute the original source count when reporting experiment denominators.

## Train and evaluate

The grouped experiments use frozen, hash-pinned assignments. Saved experiments include the grouped fine-tuned low-learning-rate candidate and a frozen-feature-extractor comparison. See [the grouped training preparation guide](../docs/GROUPED_TRAINING_V1.md) and [the model status record](../docs/PROJECT_STATUS_2026-11-17.md). The original `baseline.yaml` retains the earlier subject-ID experiment. Training is a user-run step; do not rerun it as part of routine validation.

The [Developer 1 baseline walkthrough notebook](notebooks/developer1_baseline_walkthrough.ipynb) records the local environment, grouped baseline configuration, fixed preprocessing, and saved validation-only metrics. Its inspection cells do not train or evaluate the test partition; any future training command is left for you to run manually.

~~~sh
cd ml
python -m src.train --config configs/baseline.yaml
# After freezing the model and all validation-based choices:
python -m src.train --config configs/baseline.yaml --evaluate-only
~~~

The baseline config targets an Apple Silicon Mac with MPS GPU acceleration, four persistent image-loading workers, batch size 32, and a fixed seed. It initializes MobileNetV3-Small with pretrained ImageNet weights (downloaded on the first run if absent from the PyTorch cache), freezes feature weights and batch-normalization statistics for two epochs, then fine-tunes the whole model. Set `training.device` to `auto` for CUDA/MPS/CPU selection on other machines, or explicitly select `cpu` or `cuda`. An explicitly requested unavailable device fails clearly instead of silently using CPU. Use `num_workers: 0` if multiprocessing is unavailable.

The entry point logs the selected device and setup stage immediately, batch progress every 20 batches, and total train-plus-validation time each epoch. It saves `history.jsonl`, `run-config.yaml`, `best-checkpoint.pt`, `split-manifest.csv`, and `model-metadata.json` in the ignored output directory. Choose a fresh `output_dir` for each experiment: existing checkpoints are protected from accidental overwrite. The script does not resume interrupted training. An already running process must be restarted to use source/config changes.

Training evaluates validation images only. The separate `--evaluate-only` command loads the saved checkpoint without downloading pretrained weights, verifies the data split, labels and preprocessing, then writes `test-metrics.json`. Run this only after all model and threshold decisions are frozen. Keep the original manifest and run configuration stable between training and final evaluation.

For a local macOS certificate setup error during the weight download, the installed `certifi` bundle can be selected for the current terminal session:

~~~sh
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
caffeinate -i python -u -m src.train --config configs/baseline.yaml
~~~

The binary sensitivity and specificity calculations require the configured positive label and both classes in the held-out set. Review class counts and denominators before interpreting values. The held-out test split must not be used to choose thresholds or tune the model.

## Model use boundary

The explicit ALL-score output and Option B decision rule are documented in [the ML policy implementation guide](../docs/OPTION_B_IMPLEMENTATION_V1.md). `predict` retains raw argmax semantics; `predict_with_policy` requires explicit quality/crop preconditions and the bound checkpoint. The optional local API adapter uses the versioned handoff bundle and applies the policy after the backend's quality and crop-confirmation gates.

The inference wrapper loads a local checkpoint and never downloads weights. The API does not import the ML training package; it loads the standalone inference bundle when the local provider is enabled. A C-NMC-trained model must receive a manually confirmed single-cell crop; it must not be run on arbitrary full microscope fields. Phone-capture generalization is unproven until independently labeled phone crops are evaluated.

## BCCD WBC detector prototype

The separate detector prototype uses TorchVision SSDlite with a MobileNetV3-Large backbone to propose general blood-cell boxes. The detector is trained on the BCCD train split and selected using BCCD validation only. Its source test split is not read for training or validation. The source does not establish patient/slide independence, so this experiment cannot support that claim. The detector identifies WBCs, RBCs, and platelets; it does not detect leukemia.

After running the annotation preparation in [the dataset guide](data/README.md), check the prepared train/validation data without creating a model or downloading weights:

~~~sh
source .venv/bin/activate
cd ml
python -u -m src.train_detector --config configs/bccd-ssdlite-wbc-v1.yaml --check-data-only
~~~

When ready, start the detector training yourself with:

~~~sh
python -u -m src.train_detector --config configs/bccd-ssdlite-wbc-v1.yaml
~~~

The run uses a pretrained ImageNet MobileNetV3-Large backbone, a new three-cell-class detector head, 320-pixel input, MPS by default, and a fresh ignored output folder. It keeps the BCCD test split untouched and selects the checkpoint using validation WBC AP at IoU 0.50. This small dataset and its image-level split are only for an MVP localization prototype; representative phone/microscope data and qualified annotations are needed before making target-device performance claims.
