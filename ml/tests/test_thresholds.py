import numpy as np
import pytest
from sklearn.metrics import f1_score
from src.compare_thresholds import band_metrics, cutoff_metrics, metrics


def test_cutoff_boundary_uses_all_score_and_matches_weighted_f1():
    actual = np.array([True, True, False, False])
    scores = np.array([0.5, 0.2, 0.7, 0.1])
    measured = cutoff_metrics(actual, scores, 0.5)
    assert measured["true_positive"] == measured["false_negative"] == 1
    assert measured["false_positive"] == measured["true_negative"] == 1
    assert measured["weighted_f1"] == pytest.approx(
        f1_score(actual, scores >= 0.5, average="weighted")
    )


def test_inconclusive_cases_do_not_become_negative_predictions():
    actual = np.array([True, False, True, False])
    measured = band_metrics(actual, np.array([0.1, 0.2, 0.79, 0.8]), 0.2, 0.8)
    assert measured["accepted_images"] == 2
    assert measured["inconclusive_images"] == 2
    assert measured["inconclusive_all"] == measured["inconclusive_normal"] == 1
    assert measured["accepted_metrics"]["false_negative"] == 1
    assert measured["accepted_metrics"]["false_positive"] == 1
    assert measured["accepted_metrics"]["images"] == 2
    assert measured["accepted_metrics"]["true_negative"] == 0


def test_all_abstentions_have_no_conditional_performance():
    result = band_metrics(np.array([True, False]), np.array([0.5, 0.5]), 0.2, 0.8)
    assert result["coverage"] == 0
    assert result["accepted_metrics"]["weighted_f1"] is None
    assert result["accepted_metrics"]["sensitivity"] is None


def test_class_absence_is_not_reported_as_perfect_sensitivity():
    result = metrics(np.array([False, False]), np.array([False, True]))
    assert result["sensitivity"] is None
    assert result["specificity"] == 0.5
