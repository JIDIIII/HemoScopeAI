# Grouped training v1 preparation

Prepared 15 November 2026 (Asia/Manila). Status: configuration and data checks ready; actual model training is pending the next user go signal.

## What is ready

`ml/configs/baseline-grouped-v1.yaml` selects the previously prepared `grouping-v1` / `grouped-v1` development split. It pins the SHA-256 hashes of the split, split verification, and grouping verification; the verification records also pin the original curated manifest, grouping table, and evidence. The trainer reads the saved partition assignments instead of reshuffling or regenerating them.

The original `baseline.yaml` and original baseline outputs retain their prior meanings. The new run will save under `ml/artifacts/baseline-grouped-v1/` and identify its model as `hemoscope-mobilenetv3-small-grouped-v1`.

The numerical training settings are the same as the previous baseline: pretrained MobileNetV3-Small, 224 by 224 RGB input, two frozen epochs, ten total epochs, batch size 32, learning rate 0.0003, weight decay 0.0001, seed 42, MPS, four data-loading workers. The data partition, split provenance and experiment/model identifiers change. Data-dependent class weights are recalculated from the new training partition by the same existing rule.

## Checks before model creation

The trainer validates original image integrity and byte-duplicate exclusion through the existing curated manifest checks; pinned input hashes; complete subject/group coverage; original image/subject/label/group correspondence; complete unique assignment to saved partitions; zero subject/group overlap; both classes in each partition; reviewed evidence relationships; matching partition counts; and the configured seed and grouping-policy version. Missing or changed frozen inputs fail clearly, without falling back to random splitting.

The data-only check does not select a GPU, create a model, download weights, create a training output folder, evaluate model predictions, or run optimization. From the repository root:

```sh
source .venv/bin/activate
cd ml
python -u -m src.train --config configs/baseline-grouped-v1.yaml --check-data-only
```

Expected final stage: `data_check_passed`, with `training_started: false` and `model_created: false`. Counts must remain 7,678 training / 1,486 validation / 1,289 internal test images. The saved split checksum is `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`.

The preparation evidence is saved locally at `ml/artifacts/preflight/baseline-grouped-v1.json`. It verifies the real dataset/setup; it is not a training result or a GPU benchmark.

## Next separately authorized step

After the user's next go signal, one fresh model run can be started with:

```sh
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
caffeinate -i python -u -m src.train --config configs/baseline-grouped-v1.yaml
```

The run will copy the exact split bytes and grouping/evidence verification snapshots into its new output directory, save their provenance with the checkpoint/metadata, and use validation loss to select its best checkpoint. Test evaluation remains separate and is not part of this planned training run. Existing checkpoints are protected from overwrite, and automatic resume is not implemented.

The grouped internal test is a revised development holdout; it is not a newly untouched final evaluation cohort. Grouping heuristics also do not prove true patient identity or exhaustive independence. Different validation subjects mean that scores cannot be treated as a direct like-for-like measure of model improvement over the original split.

## Checklist status

Local Step 3 is complete: a versioned configuration is connected to the frozen grouped split and passes a data-only check. The revised PDF Day 1 split-preparation item remains complete for the recorded evidence. The grouped Day 2 training/validation task is still pending; the initial baseline's completed training record remains separate.
