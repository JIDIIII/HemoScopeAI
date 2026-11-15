# HemoScope AI ML pipeline

This package scaffolds a reproducible MobileNetV3-Small transfer-learning workflow for selected-cell research images. C-NMC 2019 is the planned initial dataset. No dataset, model checkpoint, clinical metric, or sample prediction is included.

## Install and prepare data

For dataset integrity and subject-split checks only, install `python -m pip install -e "ml/[dev]"`. The tests use temporary generated images and do not need PyTorch or C-NMC files.

For training, install the additional model dependencies:

~~~sh
python -m pip install -e "ml/[train,dev]"
~~~

Review C-NMC 2019 terms and attribution before obtaining it. Prepare a manifest with image_path,label,subject_id columns and keep all images for one subject in a single train, validation, or test partition. The sample config points to a local manifest but does not download data.

See [the dataset workspace instructions](data/README.md) for the `raw/` layout, local download links, original challenge partitions, and audit/exclusion policy. The baseline config expects `data/c-nmc-2019/manifest.csv` and `data/c-nmc-2019/raw`. A local preparation report records the actual usable count after duplicate exclusions; do not substitute the original source count when reporting experiment denominators.

## Train and evaluate

The separately prepared grouped experiment uses `configs/baseline-grouped-v1.yaml` and frozen, hash-pinned assignments. See [the grouped training preparation guide](../docs/GROUPED_TRAINING_V1.md) for its data-only check and staged workflow. The original `baseline.yaml` command below retains the earlier subject-ID experiment.

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

The explicit ALL-score output and opt-in Option B decision rule are documented in [the ML policy implementation guide](../docs/OPTION_B_IMPLEMENTATION_V1.md). `predict` retains raw argmax semantics; `predict_with_policy` requires explicit quality/crop preconditions and the exact selected checkpoint. API integration is a separate step.

The inference wrapper loads a local checkpoint and never downloads weights. The backend currently has no trained model and does not import the training package. A C-NMC-trained model must receive a manually confirmed single-cell crop; it must not be run on arbitrary full microscope fields. Phone-capture generalization is unproven until independently labeled phone crops are evaluated.
