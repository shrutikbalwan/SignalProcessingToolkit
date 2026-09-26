"""Dependency-light classification and event evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    confusion_matrix: np.ndarray
    precision: np.ndarray
    recall: np.ndarray
    f1: np.ndarray
    support: np.ndarray


@dataclass(frozen=True, slots=True)
class Curve:
    x: np.ndarray
    y: np.ndarray
    thresholds: np.ndarray


@dataclass(frozen=True, slots=True)
class ThresholdResult:
    threshold: float
    precision: float
    recall: float
    f1: float
    false_positives: int


def classification_report(
    truth: np.ndarray, predicted: np.ndarray, class_count: int
) -> ClassificationReport:
    actual = np.asarray(truth, dtype=int)
    estimate = np.asarray(predicted, dtype=int)
    if actual.shape != estimate.shape or actual.ndim != 1:
        raise ValueError("truth and predicted must be equally sized one-dimensional arrays")
    if class_count <= 1 or np.any(actual < 0) or np.any(estimate < 0):
        raise ValueError("Class indexes and class_count are invalid")
    if np.any(actual >= class_count) or np.any(estimate >= class_count):
        raise ValueError("Class index exceeds class_count")
    matrix = np.zeros((class_count, class_count), dtype=int)
    np.add.at(matrix, (actual, estimate), 1)
    true_positive = np.diag(matrix).astype(float)
    predicted_positive = np.sum(matrix, axis=0)
    actual_positive = np.sum(matrix, axis=1)
    precision = np.divide(
        true_positive, predicted_positive, out=np.zeros(class_count), where=predicted_positive > 0
    )
    recall = np.divide(
        true_positive, actual_positive, out=np.zeros(class_count), where=actual_positive > 0
    )
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros(class_count),
        where=(precision + recall) > 0,
    )
    return ClassificationReport(matrix, precision, recall, f1, actual_positive)


def roc_curve(truth: np.ndarray, scores: np.ndarray) -> Curve:
    actual, values = _validate_binary(truth, scores)
    thresholds = np.r_[np.inf, np.unique(values)[::-1], -np.inf]
    true_positive_rate = []
    false_positive_rate = []
    positives = max(int(np.sum(actual)), 1)
    negatives = max(int(np.sum(~actual)), 1)
    for threshold in thresholds:
        predicted = values >= threshold
        true_positive_rate.append(np.sum(predicted & actual) / positives)
        false_positive_rate.append(np.sum(predicted & ~actual) / negatives)
    return Curve(np.asarray(false_positive_rate), np.asarray(true_positive_rate), thresholds)


def precision_recall_curve(truth: np.ndarray, scores: np.ndarray) -> Curve:
    actual, values = _validate_binary(truth, scores)
    thresholds = np.r_[np.inf, np.unique(values)[::-1], -np.inf]
    precision = []
    recall = []
    positives = max(int(np.sum(actual)), 1)
    for threshold in thresholds:
        predicted = values >= threshold
        true_positive = int(np.sum(predicted & actual))
        precision.append(true_positive / max(int(np.sum(predicted)), 1))
        recall.append(true_positive / positives)
    return Curve(np.asarray(recall), np.asarray(precision), thresholds)


def threshold_analysis(
    truth: np.ndarray, scores: np.ndarray, thresholds: np.ndarray
) -> tuple[ThresholdResult, ...]:
    actual, values = _validate_binary(truth, scores)
    results = []
    for value in np.asarray(thresholds, dtype=float):
        predicted = values >= value
        true_positive = int(np.sum(predicted & actual))
        false_positive = int(np.sum(predicted & ~actual))
        false_negative = int(np.sum(~predicted & actual))
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        results.append(ThresholdResult(float(value), precision, recall, f1, false_positive))
    return tuple(results)


def false_positive_indices(truth: np.ndarray, scores: np.ndarray, threshold: float) -> np.ndarray:
    actual, values = _validate_binary(truth, scores)
    return np.flatnonzero((values >= threshold) & ~actual)


def _validate_binary(truth: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    actual = np.asarray(truth)
    values = np.asarray(scores, dtype=float)
    if actual.ndim != 1 or values.shape != actual.shape:
        raise ValueError("truth and scores must be equally sized one-dimensional arrays")
    if not np.all(np.isin(actual, [0, 1])) or not np.all(np.isfinite(values)):
        raise ValueError("truth must be binary and scores must be finite")
    return actual.astype(bool), values
