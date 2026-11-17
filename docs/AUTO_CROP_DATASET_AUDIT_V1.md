# Automatic cell-finding dataset audit v1

Initial data-suitability audit on 17 November 2026, before the BCCD detector experiment. The later training and cross-domain results are recorded in [the smartphone detector evaluation](SMARTPHONE_DETECTOR_EVALUATION_V1.md). No source images were copied into the repository.

## Smartphone malaria smear dataset

Local source: `~/Downloads/DATASETS/Smartphone-Captures/NIH-NLM-ThinBloodSmearsPf/`.

| Annotation set | Patient folders | Full-field images | WBC annotations | Annotation type |
| --- | ---: | ---: | ---: | --- |
| Polygon Set | 33 | 165 | 51 | Cell polygons |
| Point Set | 160 | 800 | 220 | Cell centers only |
| Total | 193 distinct folder names | 965 | 271 | Mixed |

All 965 image files had a matching annotation file. The polygon set also contains 33,071 uninfected-RBC and 1,142 parasitized-RBC polygons. The point set contains 155,640 uninfected-RBC and 6,810 parasitized-RBC points. The two sets have no shared patient-folder names locally.

This is a smartphone-through-microscope **malaria** dataset. Its labels do not establish leukemia status. The 51 WBC polygons can support a very small localization prototype. The 220 WBC points provide locations but not crop dimensions or cell boundaries, so they are not ready-made bounding boxes. These counts are too small to support a reliable WBC detector or a robust independent phone-domain evaluation by themselves.

The downloaded license permits commercial and non-commercial use subject to its conditions. If the data is redistributed, retain its notice; acknowledge the U.S. National Library of Medicine and cite the listed dataset paper. Do not use NIH/NLM names to endorse the project.

## BCCD detection dataset

Local source: `~/Downloads/DATASETS/BCCD/`.

- 364 annotation XML files and 364 corresponding annotated field images were found, plus one illustrative `example.jpg`.
- The XML annotations contain 372 WBC, 4,155 RBC, and 361 platelet boxes.
- This provides full-field WBC boxes for an initial generic cell-detector prototype. It is a small dataset, and its images are not the project's own phone-and-microscope captures.
- Subject or slide identity was not verified in the local annotation files. Any split must keep each complete source image in one partition, and must not be described as patient-independent without provenance.
- The local repository includes an MIT license; retain its copyright and license notice if redistributing copies or substantial portions.

## Implication for the app

The current C-NMC classifier is trained on already-cropped cells with ALL/HEM class labels. It has no full-field ALL bounding boxes, so it cannot directly identify a “disease region” in an uncropped smear.

A feasible research prototype is a separate WBC detector that proposes cell crops, followed by the current classifier scoring each crop. The app should show the proposals and require the user to confirm a cell. A WBC proposal is a cell location, not evidence that the cell is leukemic. The current `/analyze` contract accepts a confirmed crop, so passing a full field and returning candidate boxes will require a later API/mobile contract change.

For a detector prototype, BCCD has more WBC boxes than the smartphone set. The smartphone polygon subset can be a limited cross-domain check, but 51 WBC instances are not enough for a robust performance claim. A credible target-device evaluation needs additional representative phone/microscope fields with qualified WBC annotations. Leukemia-specific localization would additionally require qualified ALL-cell boxes or masks in full-field images.

## Sources

- [NIH/NLM smartphone thin-smear dataset README](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/ReadMe.pdf)
- [NIH/NLM dataset directory and Data License Agreement](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/index.html)
- [BCCD dataset repository](https://github.com/Shenggan/BCCD_Dataset)
- [BCCD MIT license](https://github.com/Shenggan/BCCD_Dataset/blob/master/LICENSE)
- [C-NMC 2019 at TCIA](https://www.cancerimagingarchive.net/collection/c-nmc-2019/)
