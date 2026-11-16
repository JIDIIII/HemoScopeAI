# Dataset and image policy

## Approved use

C-NMC 2019 is the initial cell-level research dataset. The repository does not download or distribute its raw files. The source and local inventory review is recorded in [C-NMC Dataset Review v1](C_NMC_DATASET_REVIEW_V1.md): the TCIA collection lists CC BY 3.0 and required attribution. The download date and any institutional ethics/oversight determination are not recorded; confirm those locally before public release or publication.

Use only authorized, de-identified teaching or research images. Do not put patient names, medical record numbers, slide labels, requisition details, or other direct identifiers in manifests, upload metadata, logs, screenshots, or demonstrations.

## Subject separation

- Manifest columns are image_path, label, and subject_id.
- Split by subject, never by individual cell image.
- Check path and duplicate-content hashes, file presence, labels, subject keys, image decode, and class balance before training.
- Keep a fixed random seed and save the resulting split manifest with an experiment record.
- Do not tune decision thresholds or model settings on the held-out test partition.
- Evaluate independently labeled phone-captured cells separately from C-NMC results.

## Storage and retention

Dataset files, raw captures, checkpoints, generated splits, and metrics from private research are ignored by Git. Store shared assets only in institution-approved private storage with scoped access and a written retention/deletion plan. The API does not persist raw images or metadata. Mobile history is local metadata only and can be cleared by the user.

## Attribution and change record

Record the dataset source/version, terms reviewed, permitted use, download date, image count, label mapping, subject count, and any preprocessing. Do not redistribute source images or artifacts unless the dataset terms explicitly allow it.
