import math
from pathlib import Path

import pytest

from src.decision_policy import OPTION_B_V1, InvalidScoreError, PolicyBindingError


def decide(score):
    return OPTION_B_V1.decide(
        score,
        model_version=OPTION_B_V1.model_version,
        checkpoint_sha256=OPTION_B_V1.checkpoint_sha256,
    )


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "analysis_complete"),
        (math.nextafter(0.3, 0), "analysis_complete"),
        (0.3, "inconclusive"),
        (0.5, "inconclusive"),
        (math.nextafter(0.7, 0), "inconclusive"),
        (0.7, "review_required"),
        (1, "review_required"),
    ],
)
def test_exact_boundaries(score, expected):
    result = decide(score)
    assert result.analysis_status == expected
    assert result.decision_policy_version == "hemoscope-option-b-v1"
    assert result.all_score == score
    assert "Research" in result.message and "not a diagnosis" in result.message


@pytest.mark.parametrize(
    "score", [None, True, False, "0.4", -0.01, 1.01, float("nan"), float("inf"), -float("inf")]
)
def test_invalid_scores_raise_instead_of_becoming_low_results(score):
    with pytest.raises(InvalidScoreError):
        decide(score)


@pytest.mark.parametrize("field", ["version", "hash"])
def test_wrong_model_binding_fails(field):
    with pytest.raises(PolicyBindingError):
        OPTION_B_V1.decide(
            0.1,
            model_version="other" if field == "version" else OPTION_B_V1.model_version,
            checkpoint_sha256="bad" if field == "hash" else OPTION_B_V1.checkpoint_sha256,
        )


@pytest.fixture
def classifier():
    torch = pytest.importorskip("torch")
    from src.inference import CellClassifier

    model = object.__new__(CellClassifier)
    model.torch = torch
    model.device = torch.device("cpu")
    model.label_names = ["hem", "all"]
    model.all_index = 1
    model.model_version = OPTION_B_V1.model_version
    model.checkpoint_sha256 = OPTION_B_V1.checkpoint_sha256
    model.preprocessing = {}
    model.transform = lambda image: torch.zeros(3, 32, 32)
    model.model = lambda tensor: torch.tensor([[math.log(0.9), math.log(0.1)]])
    return model


def test_policy_uses_all_score_even_when_hem_wins_and_label_order_is_reversed(classifier):
    from PIL import Image

    result = classifier.predict_with_policy(
        Image.new("RGB", (32, 32)), quality_accepted=True, crop_confirmed=True
    )
    assert result.prediction.model_label == "hem"
    assert result.prediction.raw_model_score == pytest.approx(0.9)
    assert result.prediction.all_score == pytest.approx(0.1)
    assert result.decision.analysis_status == "analysis_complete"


@pytest.mark.parametrize("quality,crop", [(False, True), (True, False), ("true", True), (True, 1)])
def test_preconditions_stop_before_prediction(classifier, quality, crop):
    from src.inference import InferencePreconditionError

    classifier.model = lambda tensor: pytest.fail("Prediction must not run")
    with pytest.raises(InferencePreconditionError):
        classifier.predict_with_policy(None, quality_accepted=quality, crop_confirmed=crop)


def test_mismatched_checkpoint_stops_before_prediction(classifier):
    classifier.checkpoint_sha256 = "different"
    classifier.model = lambda tensor: pytest.fail("Prediction must not run")
    with pytest.raises(PolicyBindingError):
        classifier.predict_with_policy(None, quality_accepted=True, crop_confirmed=True)


@pytest.mark.parametrize("case", ["nan", "inf", "wrong_shape", "none", "integer"])
def test_bad_logits_never_produce_a_policy_result(classifier, case):
    from PIL import Image

    from src.inference import InvalidModelOutputError

    torch = classifier.torch
    outputs = {
        "nan": torch.tensor([[float("nan"), 0.0]]),
        "inf": torch.tensor([[0.0, float("inf")]]),
        "wrong_shape": torch.zeros(1, 3),
        "none": None,
        "integer": torch.tensor([[1, 2]]),
    }
    classifier.model = lambda tensor: outputs[case]
    with pytest.raises(InvalidModelOutputError):
        classifier.predict_with_policy(
            Image.new("RGB", (32, 32)), quality_accepted=True, crop_confirmed=True
        )


def test_missing_checkpoint_does_not_produce_prediction(tmp_path):
    from src.inference import CellClassifier, ModelNotAvailableError

    with pytest.raises(ModelNotAvailableError):
        CellClassifier(Path(tmp_path / "missing.pt"))
