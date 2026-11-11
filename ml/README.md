# HemoScope AI ML pipeline

This package scaffolds a reproducible MobileNetV3-Small transfer-learning workflow for selected-cell research images. C-NMC 2019 is the planned initial dataset. No dataset, model checkpoint, clinical metric, or sample prediction is included.

## Install and prepare data

For dataset integrity and subject-split checks only, install `python -m pip install -e "ml/[dev]"`. The tests use temporary generated images and do not need PyTorch or C-NMC files.

For training, install the additional model dependencies:

~~~sh
python -m pip install -e "ml/[train,dev]"
~~~

Review C-NMC 2019 terms and attribution before obtaining it. Prepare a manifest with image_path,label,subject_id columns and keep all images for one subject in a single train, validation, or test partition. The sample config points to a local manifest but does not download data.

## Train and evaluate

~~~sh
cd ml
python -m src.train --config configs/baseline.yaml
python -m pytest
~~~

The default config initializes MobileNetV3-Small without pretrained weights and uses a fixed seed. Set pretrained=true only after approving the separate ImageNet weight download. A completed run writes the best checkpoint, test metrics, split counts, preprocessing settings, and checkpoint hash under the configured ignored artifacts path.

The binary sensitivity and specificity calculations require the configured positive label and both classes in the held-out set. Review class counts and denominators before interpreting values. The held-out test split must not be used to choose thresholds or tune the model.

## Model use boundary

The inference wrapper loads a local checkpoint and never downloads weights. The backend currently has no trained model and does not import the training package. A C-NMC-trained model must receive a manually confirmed single-cell crop; it must not be run on arbitrary full microscope fields. Phone-capture generalization is unproven until independently labeled phone crops are evaluated.
