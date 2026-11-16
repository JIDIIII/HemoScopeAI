# Grouped split v1

Prepared 15 November 2026 (Asia/Manila), using [grouping policy v1](DEPENDENCY_GROUPING_POLICY_V1.md), seed 42, and the existing curated 10,453-image manifest.

## Result

| Partition | Images | Original subjects | Dependency groups | ALL images | Normal images |
| --- | ---: | ---: | ---: | ---: | ---: |
| Training | 7,678 | 50 | 38 | 5,286 | 2,392 |
| Validation | 1,486 | 10 | 9 | 909 | 577 |
| Internal test | 1,289 | 13 | 9 | 893 | 396 |
| Total | 10,453 | 73 | 56 | 7,088 | 3,365 |

Training contains 25 ALL and 13 normal dependency groups. Validation contains 5 ALL and 4 normal groups; the internal test contains 7 ALL and 2 normal groups. The small number of normal test subjects/groups limits the stability of future specificity estimates.

The 70/15/15 targets apply to dependency groups and require integer rounding. Image proportions differ because groups have different sizes. No seed search, metric optimization, training, or test prediction was used to choose this split.

## Implementation

`ml/src/dataset.py` now accepts an optional `dependency_groups` subject-to-group mapping in `split_by_subject`. Without it, the previous subject-based behavior is preserved. The new `load_dependency_groups` validates complete unique coverage, labels and retained image counts against the manifest before returning the mapping.

`ml/src/prepare_split.py` verifies the prepared mapping/evidence hashes and original manifest/audit hashes, checks image decoding and duplicate file content, creates the grouped split and verifies the results. It refuses to overwrite an existing output folder. It does not import or run model training.

To reproduce preparation into a **fresh** folder, from the repository root:

```sh
source .venv/bin/activate
cd ml
python -m src.prepare_split --output-dir data/c-nmc-2019/splits/grouped-v1-reproduction
```

Default inputs are the existing curated manifest, original `raw` image root, and `grouping-v1` folder. Default seed is 42. Image decoding/hash checks can take several seconds before a result is printed.

## Saved outputs

All outputs are local and covered by the existing dataset ignore rules:

- `ml/data/c-nmc-2019/splits/grouped-v1/split-manifest.csv`: original image path, label and subject ID, plus dependency group and partition. SHA-256: `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`.
- `verification.json`: seed, input/output hashes, partition counts, checks and limitations.
- `independent-check.json`: separate CSV read-back checks and class-specific dependency-group counts.

## Verified

- All 10,453 original curated rows appear exactly once with the same source subject IDs and labels.
- No original subject or prepared dependency group crosses partitions.
- All 7 exact-source subject-pair links and all 359 accepted near-image pair links remain within one partition.
- Both source classes occur in every partition.
- None of the 208 excluded exact-duplicate copies has returned.
- Seed 42 reproduces identical assignments.
- The original manifest, original split, original training configuration, and original/preserved baseline artifacts retain their recorded hashes.

Regression tests exercise group separation and reproducibility, rejection of missing classes, and failure for incomplete, extra, blank, duplicate, mislabeled or count-mismatched mappings. Existing training tests still pass on CPU; the GPU-only check is skipped when the restricted environment cannot expose MPS. This step changes data preparation, not GPU execution.

## Status and next boundary

The revised Day 1 split-generation and leakage-check work is complete for the recorded grouping policy. This establishes separation of **known reviewed relationships**, not proof of true patient independence or exhaustive absence of other similar images.

The original internal test results have already informed this data review; this revised internal test is a development holdout, not a newly independent final assessment cohort.

The existing training command/configuration still uses the previous subject-ID setup. The next separately authorized step is to prepare a versioned training configuration and connect the trainer to this frozen split and its recorded hashes. Training has not started, and this step has not changed model weights, learning rate, thresholds or API behavior.
