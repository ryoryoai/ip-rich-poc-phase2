"""Normalization helpers for company and product names."""

from __future__ import annotations

import re
import unicodedata


_CORP_DESIGNATORS = [
    r"\u682a\u5f0f\u4f1a\u793e",  # 株式会社
    r"\u6709\u9650\u4f1a\u793e",  # 有限会社
    r"\u5408\u540c\u4f1a\u793e",  # 合同会社
    r"\u5408\u540d\u4f1a\u793e",  # 合名会社
    r"\u5408\u8cc7\u4f1a\u793e",  # 合資会社
    r"\(\u682a\)",  # (株)
    r"\(\u6709\)",  # (有)
]

_EN_DESIGNATORS = [
    r"\bco\.?\b",
    r"\bco\.?\s*ltd\.?\b",
    r"\bcorp\.?\b",
    r"\binc\.?\b",
    r"\bltd\.?\b",
    r"\bcorporation\b",
    r"\bcompany\b",
    r"\bholdings?\b",
]


_NORMALIZE_PATTERN = re.compile(
    "[\\s\\u3000\\-\\u2010-\\u2015\\u30fc\\u00b7\\u30fb\\.,/()\\[\\]{}]+"
)


def _normalize_text(value: str) -> str:
    """Normalize unicode width/case and strip common separators."""
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = _NORMALIZE_PATTERN.sub("", normalized)
    return normalized


def normalize_company_name(name: str) -> str:
    """Normalize company names for matching."""
    if not name:
        return ""

    normalized = unicodedata.normalize("NFKC", name).lower()

    for pattern in _CORP_DESIGNATORS:
        normalized = re.sub(pattern, "", normalized)

    for pattern in _EN_DESIGNATORS:
        normalized = re.sub(pattern, "", normalized)

    return _normalize_text(normalized)


def normalize_product_name(name: str) -> str:
    """Normalize product names/model strings for matching."""
    return _normalize_text(name or "")


def normalize_keyword_term(term: str) -> str:
    """Normalize technical keyword terms for matching."""
    return _normalize_text(term or "")
