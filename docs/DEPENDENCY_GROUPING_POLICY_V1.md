# Dependency grouping policy v1

Prepared: 15 November 2026, Asia/Manila. Policy ID: `grouping-v1`.

**Status: prepared, not applied to training or splitting.**

## Plain-language explanation

Some C-NMC images assigned to different source subject IDs are identical or nearly identical. The same or related image content can therefore appear on both sides of a subject-ID-only split. Removing byte-identical copies reduced that problem, but retained near-image relationships remain.

For this policy, related subjects receive one additional `dependency_group` key. A future splitter must place the entire group in one partition. The original subject IDs and labels remain unchanged. A dependency group records an image-content relationship; it does not establish that the members are the same patient.

For example, `UID_51`, `UID_75`, and `UID_78` all map to `dg_032`. Their original subject IDs remain in the data. A future split must place all three together in training, validation, or testing.

This step prepares the rule and mapping. The existing splitter still uses subject IDs, and the existing baseline remains the original subject-ID-only experiment.

## Scope and fixed evidence

The policy uses the original labeled C-NMC training source, consisting of 10,661 images and 73 subject IDs. Its active curated manifest has 10,453 images after excluding all 208 copies in the 104 recorded exact-duplicate groups. Those exclusions remain unchanged.

Inputs come from the previously completed local review under `ml/artifacts/diagnostics/review-v1/`:

- `exact-subject-pairs.csv`: seven subject-pair links supported by 99 cross-subject exact-byte duplicate groups. These source links remain relevant even though the duplicate copies themselves were excluded.
- `near-duplicate-full-resolution-check.csv`: 364 cross-subject candidate image pairs from the bounded similarity screen. Of these, 359 pass the original-resolution foreground-difference rule below; five do not and contribute no near-pair edge under this policy.
- `proposed-subject-groups-conservative.csv`: the earlier proposal, used to check that this preparation reproduces its component membership.
- `source-image-inventory.csv`: source image paths, labels and original subject IDs, used to verify the active manifest and mapping.

Input paths and SHA-256 hashes are recorded in the local `provenance.json`. This policy does not use model accuracy, scores, or errors to decide which subjects are linked. The earlier image audit inspected metadata and image content from the original internal partitions, so it does not establish a newly untouched final test cohort. Official challenge sets are outside this mapping.

## Group construction

1. Create one graph vertex for every original subject ID in the active manifest.
2. Add an undirected edge for each recorded cross-subject exact-byte source relationship.
3. Add an undirected edge for each reviewed near-image candidate satisfying all of:
   - DCT perceptual-hash Hamming distance at most 4 on an unrotated 32 by 32 grayscale thumbnail.
   - Mean absolute RGB difference at most 0.01 on a 64 by 64 thumbnail, with intensity normalized to 0 through 1.
   - Thumbnail union-foreground RGB difference at most 0.02 and foreground correlation at least 0.98.
   - Equal original decoded image dimensions and original-resolution union-foreground RGB difference at most 0.02.
4. Treat each connected component as one dependency group. If A links to B and B links to C, A, B and C stay together even without a direct A-to-C link.
5. Give a subject with no recorded links a group of its own. This means no link was found in the reviewed evidence, not that independence was proved.
6. Assign stable `dg_001` through `dg_056` identifiers by sorting components by their lexicographically smallest original subject ID. IDs are identifiers within this policy version, not patient IDs.

Foreground in these measurements means the union of pixels whose maximum RGB channel exceeds 16 on a 0 through 255 scale. It is a heuristic foreground mask, not a biological cell annotation. The earlier review's very-close subset (original foreground difference at most 0.001) is recorded separately as stronger near-image evidence; it does not change the broader v1 inclusion rule.

The component-level `evidence_basis` can contain `exact_byte_source_link`, `screened_near_image_candidate`, or both. Individual subject-pair counts and the strongest observed near-image difference are retained in `group-evidence.csv`. A component-level basis does not mean that every pair of subjects has a direct link.

## Prepared results

| Item | Count |
| --- | ---: |
| Original subject IDs | 73 |
| Prepared dependency groups | 56 |
| Groups containing multiple subjects | 10 |
| Single-subject groups | 46 |
| Original ALL / normal subject IDs | 47 / 26 |
| ALL / normal dependency groups | 37 / 19 |
| Retained ALL / normal images | 7,088 / 3,365 |
| Retained images in total | 10,453 |

All prepared groups currently contain one source class. This is an observed property of this dataset and evidence, not permission to merge labels or a universal requirement for future datasets.

## Files and verification

Local outputs are stored under `ml/data/c-nmc-2019/grouping-v1/`, covered by the existing dataset ignore rules:

- `subject-groups.csv`: exactly one row per subject, with `subject_id`, `dependency_group`, original `label`, retained image count and evidence basis.
- `group-summary.csv`: component membership, class, image counts and evidence counts.
- `group-evidence.csv`: the 17 contributing subject-pair edges and their exact/near evidence counts.
- `verification.json`: checks, counts, output hashes and explicit prepared-only status.
- `provenance.json`: input and protected-file hashes.
- `prepare_groups.py`: a saved copy of the preparation procedure, which refuses to overwrite an existing v1 folder.

Preparation verifies complete and unique coverage of all 73 subjects; original subject/label correspondence for all 10,453 active image rows; membership agreement with the prior conservative proposal; one group for each evidence link; continued exclusion of all 208 recorded duplicate copies; and unchanged active manifest, original split, training code, configuration and baseline artifacts.

It does **not** yet verify separation across new partitions, class coverage in each new partition, or new partition counts. Those checks require a subsequent splitter implementation and split-generation step.

## Assumptions, limitations and future use

The near-image links are heuristic candidate relationships. Conservatively keeping their subjects together may combine genuinely different people. It trades some effective sample size for a guard against image reuse; true patient identity remains unresolved. No biological label or source identity is corrected by this policy.

The bounded similarity scan does not exhaustively find rotations, shifts, alternative crops or other image transformations. Fifty-six dependency groups do not establish 56 statistically independent patients, and a future grouped score is not automatically proof of generalization.

For subsequent work, join the mapping on `subject_id` and split on the additional `dependency_group` key. Keep the original columns. Verify zero subject/group overlap and zero reviewed evidence links crossing partitions, both source classes in each partition, and saved image/subject/group counts. An absent mapping, duplicate mapping, changed manifest, or mismatched policy hash must cause a clear failure. Data proportions must not take precedence over keeping groups intact.

Do not overwrite v1 when evidence or membership changes; prepare a new version with a change record. Save policy and mapping hashes with future experiments. Keep previously observed test results identified appropriately and reserve separately audited untouched data for the eventual final assessment.

## Developer 1 checklist status after this step

The local step **document grouping rule and prepare mapping** is complete. The PDF Day 1 dataset-split and leakage-check item remains **partial for the revised protocol** until the splitter consumes the mapping and a new split passes the partition-level checks. This step does not complete model retraining, uncertainty selection, API agreement, or backend handoff.
