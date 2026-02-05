"""Normalization utilities for JP Patent Index."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class NormalizedNumber:
    """Normalized representation of a JP patent-related number."""

    raw: str
    number_norm: str
    number_base: str
    number_type: str  # application/publication/patent
    country: str = "JP"
    kind: Optional[str] = None


def normalize_applicant_name(name: str) -> str:
    """Normalize applicant name using a simple rule-based approach."""
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"[\s\u3000]+", "", name)
    return name.upper()


def _build_number_norm(digits: str, kind: Optional[str]) -> tuple[str, str]:
    base = f"JP{digits}"
    if kind:
        return f"{base}{kind}", base
    return base, base


def normalize_number(
    input_str: Optional[str],
    number_type_hint: Optional[str] = None,
) -> Optional[NormalizedNumber]:
    """Normalize JP patent-related number formats."""
    if not input_str:
        return None

    raw = input_str.strip()
    if not raw:
        return None

    value = raw.replace("　", " ").strip()

    # 特許第1234567号
    match = re.match(r"特許第(\d+)号", value)
    if match:
        digits = match.group(1)
        norm, base = _build_number_norm(digits, "B2")
        return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type="patent", kind="B2")

    # 特開2020-123456 / 特表2020-123456 / 特公 / 特許
    match = re.match(r"(特開|特表|特公|特願)(\d{4})[-‐－](\d+)", value)
    if match:
        kind_hint = match.group(1)
        digits = f"{match.group(2)}{match.group(3)}"
        if kind_hint == "特願":
            norm, base = _build_number_norm(digits, None)
            return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type="application")
        if kind_hint == "特公":
            norm, base = _build_number_norm(digits, "B2")
            return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type="patent", kind="B2")
        norm, base = _build_number_norm(digits, "A")
        return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type="publication", kind="A")

    # JP1234567B2 / JP2020123456A
    match = re.match(r"JP(\d+)([A-Z]\d?)?", value, re.IGNORECASE)
    if match:
        digits = match.group(1)
        kind = match.group(2).upper() if match.group(2) else None
        number_type = number_type_hint or ("patent" if kind and kind.startswith("B") else "publication")
        norm, base = _build_number_norm(digits, kind)
        return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type=number_type, kind=kind)

    # PCT/JP2020/123456
    match = re.match(r"PCT/JP(\d{4})/(\d+)", value, re.IGNORECASE)
    if match:
        digits = f"{match.group(1)}{match.group(2)}"
        norm, base = _build_number_norm(digits, None)
        return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type="application")

    # Plain digits
    match = re.match(r"^(\d{6,12})$", value)
    if match:
        digits = match.group(1)
        inferred_type = number_type_hint or "patent"
        kind = "B2" if inferred_type == "patent" else ("A" if inferred_type == "publication" else None)
        norm, base = _build_number_norm(digits, kind)
        return NormalizedNumber(raw=raw, number_norm=norm, number_base=base, number_type=inferred_type, kind=kind)

    return None
