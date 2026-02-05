"""Tests for JP gazette parser."""

from pathlib import Path

import pytest

from app.parse.jp_gazette_parser import (
    parse_jp_gazette_xml,
    normalize_claim_text,
)


@pytest.fixture
def sample_xml_path() -> Path:
    """Return path to sample XML file."""
    return Path(__file__).parent / "fixtures" / "sample_jp_b2.xml"


class TestNormalizeClaimText:
    """Tests for claim text normalization."""

    def test_strips_whitespace(self) -> None:
        text = "  Some claim text  "
        assert normalize_claim_text(text) == "Some claim text"

    def test_collapses_blank_lines(self) -> None:
        text = "Line 1\n\n\n\nLine 2"
        assert normalize_claim_text(text) == "Line 1\n\nLine 2"

    def test_handles_empty_string(self) -> None:
        assert normalize_claim_text("") == ""

    def test_preserves_single_newlines(self) -> None:
        text = "Line 1\nLine 2\nLine 3"
        assert normalize_claim_text(text) == "Line 1\nLine 2\nLine 3"


class TestParseJpGazetteXml:
    """Tests for XML parsing."""

    def test_parses_sample_xml(self, sample_xml_path: Path) -> None:
        result = parse_jp_gazette_xml(sample_xml_path)

        assert result is not None
        assert result["country"] == "JP"
        assert result["doc_number"] == "1234567"
        assert result["kind"] == "B2"
        assert len(result["claims"]) == 2

    def test_extracts_claim_1(self, sample_xml_path: Path) -> None:
        result = parse_jp_gazette_xml(sample_xml_path)

        assert result is not None
        claim_1 = next(c for c in result["claims"] if c["claim_no"] == 1)
        assert "物品を製造する方法" in str(claim_1["claim_text_norm"])

    def test_returns_none_for_invalid_file(self, tmp_path: Path) -> None:
        invalid_file = tmp_path / "invalid.xml"
        invalid_file.write_text("not xml content")

        result = parse_jp_gazette_xml(invalid_file)
        assert result is None
