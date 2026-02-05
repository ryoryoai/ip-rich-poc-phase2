"""Tests for JP Index status derivation."""

from types import SimpleNamespace

from app.jp_index.status import derive_status


def test_status_derivation_prefers_expired() -> None:
    events = [
        SimpleNamespace(id="1", event_type="GRANTED", event_date="2020-01-01"),
        SimpleNamespace(id="2", event_type="EXPIRED", event_date="2025-01-01"),
    ]
    derived = derive_status(events)
    assert derived.status == "expired"
    assert "expired" in derived.reason


def test_status_default_when_no_events() -> None:
    derived = derive_status([])
    assert derived.status == "pending"
