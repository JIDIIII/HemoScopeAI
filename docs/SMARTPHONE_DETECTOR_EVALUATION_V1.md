# Smartphone WBC detector check v1

Date: 17 November 2026. This was a cross-domain diagnostic of the saved BCCD detector. It was not used for training, score-threshold selection, or model selection.

## Result

The BCCD SSDlite MobileNetV3-Large checkpoint (`hemoscope-bccd-ssdlite-wbc-v0`, SHA-256 `027db6276b8cf852944aa895615817b98212cbe9c1574375f470388cfa6d75b8`) was evaluated on the NIH/NLM Thin Blood Smear smartphone dataset's Polygon Set. The evaluated set contained 165 full-field smartphone microscope images from 33 patient folders and 51 White Blood Cell polygons. Polygon outlines were converted to their enclosing rectangles for IoU comparison; all image and annotation dimensions were checked.

At the detector's predeclared candidate threshold 0.25 and IoU 0.50:

| Measure | Result |
| --- | ---: |
| WBC AP50 | 0.00 |
| WBC true positives | 0 |
| WBC false positives | 221 |
| WBC false negatives | 51 |
| WBC precision | 0.00 |
| WBC recall | 0.00 |
| WBC false positives per field | 1.34 |

The result reproduces the previous smartphone-image check. The reproducible evaluator is `ml/src/evaluate_smartphone_detector.py`; it reads the locally downloaded dataset in place, blocks network access while rebuilding the saved architecture, writes only aggregate metrics, and refuses to overwrite an existing report. Its ignored output is `ml/artifacts/diagnostics/bccd-smartphone-check-v1.json`.

From the `ml` directory, it can be rerun only as a diagnostic (do not use this set to tune the threshold):

```sh
python -m src.evaluate_smartphone_detector \
  --dataset-root "$HOME/Downloads/DATASETS/Smartphone-Captures/NIH-NLM-ThinBloodSmearsPf/Polygon Set"
```

## Interpretation and product decision

The detector worked on its BCCD validation source but did not localize WBCs on this smartphone malaria domain. This indicates a substantial domain-transfer failure for the intended image style. The smartphone set is small and concerns malaria; its WBC labels do not indicate leukemia. It is not evidence that BCCD or malaria images can train or validate the ALL/HEM classifier.

Do not connect this detector to the app as an automatic cropper. Keep the current manually confirmed crop flow. Do not send WBC proposals into the leukemia classifier as if they were disease regions. Reconsider proposals only after collecting representative, authorized phone/microscope images with qualified WBC annotations and independently checking detector performance on a separate target-device cohort. Leukemia-region localization would require separate, qualified ALL-cell boxes or masks in full-field images.

The local downloaded source README and dataset audit describe the source terms and attribution requirements. No dataset images, labels or private files are included in this report or Git.
