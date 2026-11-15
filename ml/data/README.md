# Research dataset workspace

Keep authorized dataset copies in the local layout below. Raw downloads and generated manifests are ignored by Git; the repository does not distribute or automatically download datasets. Review each source's terms and attribution requirements before use.

```text
ml/data/
  c-nmc-2019/
    raw/                    # Original C-NMC folders, unchanged
      C-NMC_training_data/
      C-NMC_test_prelim_phase_data/
      C-NMC_test_final_phase_data/
      C-NMC_Leukemia.sums
    manifest.csv            # Audited, labeled training images only
    source-audit.json       # Local source counts and duplicate groups
    preparation-report.json # Local audit and exclusion summary
    split-manifest.csv      # Candidate subject-separated partitions
  bccd/raw/
  multi-focus-wbc/raw/
  smartphone-captures/raw/
  smear-quality/raw/
```

`raw` may be a real directory or a local symbolic link to an existing download, avoiding a second copy of large datasets. The current workstation uses links to folders under `~/Downloads/DATASETS`. These links are ignored and are not part of the repository. Other developers must supply their own local copies or links. Moving or deleting a link's original download will break that link. Keep generated manifests beside `raw`, rather than writing into the original download.

The baseline config reads images from `data/c-nmc-2019/raw` and the manifest from `data/c-nmc-2019/manifest.csv`, relative to `ml/`.

The training manifest is a CSV with these columns:

~~~text
image_path,label,subject_id
~~~

Paths are relative to the configured image root. Use the source dataset's subject keys only to create subject-disjoint partitions. Do not add patient names or other direct identifiers. Review the original dataset documentation for its intended labels and permitted use before constructing the manifest.

For C-NMC training filenames, `UID_11_10_1_all.bmp` belongs to subject `UID_11`, while `UID_H11_10_1_hem.bmp` belongs to subject `UID_H11`. Preserve the `H` distinction and normalize its case. Filename naming is documented in the [official C-NMC README](https://www.cancerimagingarchive.net/wp-content/uploads/CNMC_readme.pdf).

Use only `C-NMC_training_data` to construct the initial baseline manifest, with labels `all` and `hem`. Keep the supplied preliminary and final challenge sets separate. The final set has no supplied per-image ground truth and cannot provide local accuracy metrics without a separate authoritative label source. The baseline's internal train/validation/test split is made by subject from the training manifest; it is not the challenge's final test set.

Audit checksums against the supplied `C-NMC_Leukemia.sums`, verify image decoding, and group identical file contents using SHA-256 before training. The local preparation policy excludes every copy in each exact-byte duplicate group from the training manifest, while preserving the original download. Record the groups in `source-audit.json` and the exclusions, retained counts, seed, and manifest hash in `preparation-report.json`. Duplicate images assigned to different source subject IDs indicate metadata uncertainty; removing exact duplicates does not establish that all near-duplicates or subject-mapping problems are resolved. The training entry point checks the curated manifest again and regenerates its internal split using the configured seed.

Keep the other datasets separate from the C-NMC classifier. BCCD supports cell detection experiments; the remaining folders require source and annotation verification before focus, quality, or acquisition experiments. A folder called `smartphone-captures` does not establish that images came from this project's phone/microscope setup. Do not map malaria or quality annotations into ALL/normal labels.

Generated manifests, images, cached data, and labels are ignored by Git. A header-only example is available as manifest.example.csv.
