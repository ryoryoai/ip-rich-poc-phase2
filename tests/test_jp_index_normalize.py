"""Tests for JP Index normalization utilities."""

from app.jp_index.normalize import normalize_number


def test_normalize_patent_number_jp_format() -> None:
    normalized = normalize_number("特許第1234567号")
    assert normalized is not None
    assert normalized.number_norm == "JP1234567B2"
    assert normalized.number_type == "patent"


def test_normalize_application_number() -> None:
    normalized = normalize_number("特願2020-123456")
    assert normalized is not None
    assert normalized.number_norm == "JP2020123456"
    assert normalized.number_type == "application"


def test_normalize_publication_number() -> None:
    normalized = normalize_number("特開2020-123456")
    assert normalized is not None
    assert normalized.number_norm == "JP2020123456A"
    assert normalized.number_type == "publication"
