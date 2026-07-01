"""Unit tests for embedding vector validation."""

from domain.embedding import EmbeddingValidationErrorType, EmbeddingValidator


def test_valid_vector_passes() -> None:
    validator = EmbeddingValidator(expected_dimension=4)

    report = validator.validate([0.1, -0.2, 0.3, -0.4])

    assert report.valid is True
    assert report.errors == []


def test_empty_vector_fails_early() -> None:
    validator = EmbeddingValidator(expected_dimension=4)

    report = validator.validate([])

    assert report.valid is False
    assert report.errors == [EmbeddingValidationErrorType.EMPTY_VECTOR]


def test_wrong_dimension_fails() -> None:
    validator = EmbeddingValidator(expected_dimension=4)

    report = validator.validate([0.1, 0.2])

    assert report.valid is False
    assert EmbeddingValidationErrorType.WRONG_DIMENSION in report.errors


def test_non_finite_value_fails() -> None:
    validator = EmbeddingValidator(expected_dimension=3)

    report = validator.validate([0.1, float("nan"), 0.2])

    assert report.valid is False
    assert EmbeddingValidationErrorType.NON_FINITE_VALUE in report.errors


def test_zero_vector_fails() -> None:
    validator = EmbeddingValidator(expected_dimension=3)

    report = validator.validate([0.0, 0.0, 0.0])

    assert report.valid is False
    assert EmbeddingValidationErrorType.ZERO_VECTOR in report.errors
