# C-NMC 2019 dataset review v1

**Reviewed:** 2026-11-15  
**Source:** The Cancer Imaging Archive (TCIA), C-NMC 2019, Version 1  
**Purpose:** Developer 1 source, access, label, count, and attribution record

This records the terms and metadata visible on the official TCIA collection page and its dataset README, alongside the local source audit. It is not an institutional legal or research-ethics approval.

## Access and use

TCIA lists the C-NMC 2019 images and README as **CC BY 3.0** and marks a data citation as required. The collection download is listed as BMP, CSV, and PDF, approximately 10.44 GB, through TCIA's Aspera download service. The collection page is marked public. See the [TCIA C-NMC collection page](https://www.cancerimagingarchive.net/collection/c-nmc-2019/) and the [official dataset README](https://wiki.cancerimagingarchive.net/download/attachments/52758223/CNMC_readme.pdf?api=v2&modificationDate=1559220477330&version=1).

CC BY 3.0 allows sharing and adaptation with attribution, a license link, and an indication of changes when a derivative is made. It does not imply endorsement, and Creative Commons notes that privacy, publicity, moral, or other rights may require separate consideration. TCIA separately prohibits using its data, alone or with other information, to identify or contact participants; it also directs investigators conducting human-subjects research to comply with applicable requirements. These rules are summarized in the [TCIA data-use policy](https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/) and the [CC BY 3.0 deed](https://creativecommons.org/licenses/by/3.0/).

For this project, the raw download, image manifest, and model artifacts remain local and Git-ignored. Do not add the source images to a repository or distribute them through a demo. The local files pass the existing checksum audit, but **the owner identifies themselves as the downloader, and a supplied Aspera transfer screenshot records completion on 2026-11-13 (see follow-up below)** in the project files. The exact downloaded copy has not been compared with a separate TCIA release manifest beyond the included checksum file.

## Labels and subject identifiers

The official README describes segmented cell images labeled as leukemic B-lymphoblasts versus normal B-lymphoid precursors, with labels marked by an expert oncologist. The source filename conventions are:

- `UID_P_N_C_all`: `all` is the ALL cancer class; `UID_P` carries the source subject key.
- `UID_HS_N_C_hem`: `H` denotes a healthy/normal subject, `S` is that subject's ID, and `hem` denotes the normal cell class.

The local manifest uses `all` and `hem`, preserves source subject IDs, and keeps the `H` prefix (for example, `UID_11` and `UID_H11` remain distinct). These are dataset cell labels, not patient-level diagnostic outputs. The source README says the cells were segmented and that stain normalization was applied by the dataset authors; the model's separate resize and tensor normalization are recorded in its run configuration.

## Official source counts

TCIA's challenge-phase counts are:

| Phase | Images | ALL | Normal / HEM | Source subjects |
| --- | ---: | ---: | ---: | ---: |
| Training | 10,661 | 7,272 | 3,389 | 73 (47 ALL, 26 normal) |
| Preliminary test | 1,867 | 1,219 | 648 | 28 (13 ALL, 15 normal) |
| Final test | 2,586 | Not supplied per image | Not supplied per image | 17 (9 ALL, 8 normal) |

The final challenge phase has no supplied per-image ground-truth labels, so it cannot support local accuracy calculations without a separate authoritative label source. The challenge-phase image counts sum to **15,114**.

There is a source-count discrepancy to preserve in future reporting: TCIA's collection summary separately lists **15,135 images**, 21 more than the three phase counts. A local inventory found 10,661 training BMPs, 1,867 preliminary-test BMPs, and 2,586 final-test BMPs, totaling 15,114. The supplied checksum file has 15,115 records; that is a checksum-record count, not the phase image total. The discrepancy has not been reconciled with TCIA, so do not describe either total as a corrected official count.

## Local preparation and active training data

The downloaded directory exists at the configured local `raw/` link. The saved preparation report records **15,115 checksum entries checked, zero missing entries, zero checksum mismatches, and successful image decoding after exclusions**. The source training subset has the official 10,661 images and 73 IDs.

The active training manifest is deliberately smaller because the project audit excluded every copy in each exact-byte duplicate group:

| Local derivative | Images | ALL | HEM | Source subject IDs |
| --- | ---: | ---: | ---: | ---: |
| Curated training manifest | 10,453 | 7,088 | 3,365 | 73 |
| Grouped split — train | 7,678 | 5,286 | 2,392 | 50 |
| Grouped split — validation | 1,486 | 909 | 577 | 10 |
| Grouped split — held-out partition | 1,289 | 893 | 396 | 13 |

The source training set is approximately **68.21% ALL / 31.79% normal**. After the recorded exclusions, the active manifest is **67.81% ALL / 32.19% HEM**.

The 10,453-image manifest has SHA-256 `eadebea54de86becaaa166228d9c8f366977d77c7c02a2b809317a2cb7004c71`. The grouped split has SHA-256 `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`. Training and validation rows come from the C-NMC training phase only. The held-out partition is a development split from that training source; it is not the challenge's final test phase or a newly collected independent cohort.

The exact-duplicate audit found **104 groups / 208 image copies**, of which **99 groups cross source subject IDs**. Those copies remain excluded and the original IDs remain unchanged. The official README describes the source folds as subject-separated; the local cross-ID duplicate evidence means that statement does not resolve the observed relationships in this copy. It does not prove that different IDs are the same patient. A later conservative grouping policy keeps reviewed near-image relationships together when splitting; those heuristic groups also do not prove common patient identity. See [the grouping policy](DEPENDENCY_GROUPING_POLICY_V1.md) and [the frozen split record](GROUPED_SPLIT_V1.md).

## Required attribution record

The current TCIA collection page requests the dataset citation, a related publication citation, and the general TCIA citation. Retain these in any public report or presentation that uses the dataset:

1. Mourya, S., Kant, S., Kumar, P., Gupta, A., & Gupta, R. (2019). *ALL Challenge dataset of ISBI 2019 (C-NMC 2019)* (Version 1) [dataset]. The Cancer Imaging Archive. [https://doi.org/10.7937/tcia.2019.dc64i46r](https://doi.org/10.7937/tcia.2019.dc64i46r).
2. Gehlot, S., Gupta, A., & Gupta, R. (2020). *SDCT-AuxNetθ: DCT augmented stain deconvolutional CNN with auxiliary classifier for cancer diagnosis*. Medical Image Analysis, 61, 101661. [https://doi.org/10.1016/j.media.2020.101661](https://doi.org/10.1016/j.media.2020.101661).
3. Clark, K., Vendt, B., Smith, K., Freymann, J., Kirby, J., Koppel, P., Moore, S., Phillips, S., Maffitt, D., Pringle, M., Tarbox, L., & Prior, F. (2013). *The Cancer Imaging Archive (TCIA): Maintaining and Operating a Public Information Repository*. Journal of Digital Imaging, 26(6), 1045–1057. [https://doi.org/10.1007/s10278-013-9622-7](https://doi.org/10.1007/s10278-013-9622-7).

When sharing an adapted manifest or results, identify the source as C-NMC 2019 Version 1, link to the CC BY 3.0 license and collection DOI, and state that duplicate copies were excluded and images were resized/normalized for the model. Do not imply that TCIA or the data authors endorse HemoScope AI.

## Oversight and download confirmation follow-up - 2026-11-18

This follow-up records the handoff owner's local investigation. It does not grant institutional approval or revalidate the earlier license review. Requests are prepared in [the confirmation tracker](C_NMC_CONFIRMATION_TRACKER_2026-11-18.md) but have **not been sent**. No external reply has been received as part of this follow-up.

| Field | Evidence-backed status |
| --- | --- |
| Dataset identity | Existing source review identifies C-NMC 2019 Version 1, TCIA, DOI `10.7937/tcia.2019.dc64i46r`. Local folder names are consistent with the three challenge phases; they do not independently establish the exact release downloaded. |
| Download completion date | **2026-11-13, 9:02:08 AM**, as displayed in the supplied transfer screenshot. Timezone and transfer start time are not shown; no timezone conversion was applied. |
| Original downloader | **Confirmed by owner statement in this chat on 2026-11-18:** the current handoff assignee downloaded the dataset. This is a self-report, not an independently verified transfer record. |
| Retrieval method | **IBM Aspera**, supported by the screenshot application field `IBM Aspera - Aspera`, title `PKG - C-NMC 2019`, status `Downloaded`, and progress `100%`. |
| Receipt/log | Owner subsequently supplied a transfer-info screenshot in this chat. A local Git-ignored evidence copy is saved at `ml/artifacts/provenance/c-nmc-aspera-transfer-2026-11-13.png`; see interpretation below. |
| Institutional determination | **Pending - request not sent**. Institution, recipient, decision, decision date, reference, scope, conditions and written evidence location are not yet supplied. |
| Intended sharing and institutional limits | Owner confirms HemoScope AI is intended for submission to Huawei ICT Competition 2026-2027. The Innovation Competition track is confirmed; the team reports having no school adviser yet. Country/region, submission materials, public availability and model-weight sharing remain unconfirmed. School affiliation and an alternative oversight contact are not yet supplied. Competition participation does not itself establish an institutional determination. Existing attribution requirements above remain recorded. |

### Supplied transfer evidence

Screenshot SHA-256: `473053e51bdb58f0fc6aefe457484800c13fb9e7e9ee9b8ed88312e8af71ea4e`. It displays 15,120 files attempted/completed and 9.7 GB written. These are transfer UI values, not verified image counts or checksum results. The UI also displays 1.2 MB expected; that discrepancy is unresolved and is not used to assess integrity. The screenshot does not show a source URL/DOI or explicit release version, so it does not independently verify TCIA origin or Version 1.

The displayed destination is under `D:/Downloads/PKG - C-NMC 2019/`, whereas the inspected current folder is under `D:/Downloads/DATASETS/MICROSCOPE/PKG - C-NMC 2019/`. The owner supplied the screenshot as evidence for their download, but the move/copy history and byte identity between those locations were not independently verified. Network/account/transfer identifiers are retained only in the ignored original evidence image, not transcribed here.

### Records checked and integrity evidence boundary

On 2026-11-18, the repository source review, dataset policy, project checklist, `ml/data/README.md`, grouping/split documentation, and the source review's Git history were inspected. A targeted listing of the local Downloads dataset directories located `D:/Downloads/DATASETS/MICROSCOPE/PKG - C-NMC 2019/`. It contains the three challenge-phase directories and `C-NMC_Leukemia.sums`. A recursive filename search for PDF, TXT, LOG, JSON, SUMS, HTML and EML records found only the checksum file. No email, browser history or personal account records were inspected. This is a scoped search, not proof that no receipt exists elsewhere.

The existing preparation/checksum results above are historical project records, not checks rerun in this follow-up. Their documented evidence paths are `ml/data/c-nmc-2019/source-audit.json`, `ml/data/c-nmc-2019/preparation-report.json`, and `ml/data/c-nmc-2019/splits/grouped-v1/verification.json`; see [dataset workspace instructions](../ml/data/README.md) and [the frozen split record](GROUPED_SPLIT_V1.md). The `ml/data/c-nmc-2019/` directory, including its configured `raw/` link and saved audit files, is absent from this checkout. The external dataset folder was inspected in place; checksums, counts and image decoding were not rerun. Recover the original audit evidence from its owner if needed; do not treat the supplied checksum file alone as a successful verification.

No dataset, manifest, split, model or application changes were made for this follow-up. Keep receipts and determinations containing personal/account information in suitable private storage; commit only a non-sensitive summary and evidence locator, never raw images, credentials or sensitive receipts.

## Remaining confirmations

- Ask the course supervisor or institution whether this project's intended use requires ethics or research-oversight review; the public license does not answer that institutional question.
- Download completion date and Aspera method are now supported by the supplied screenshot. Exact source/version and the destination move/copy history remain independently unverified; retain these limits rather than inferring them from the package title.
- If a public release or publication is planned, verify the citation list against TCIA's current collection page and the dataset README at that time.
- Do not claim that the source's reported subject-level separation resolves the local cross-subject duplicate evidence. The grouping record addresses known reviewed image relationships, not confirmed patient identities or every possible near-duplicate.
