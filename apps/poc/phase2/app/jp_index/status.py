"""Status derivation for JP Patent Index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


FINAL_STATUS_PRIORITY = {
    "expired": 100,
    "withdrawn": 95,
    "abandoned": 90,
    "rejected": 85,
    "granted": 80,
    "pending": 10,
    "unknown": 0,
}

EVENT_STATUS_MAP = {
    "EXPIRED": "expired",
    "LAPSED": "expired",
    "CANCELLED": "expired",
    "WITHDRAWN": "withdrawn",
    "ABANDONED": "abandoned",
    "REJECTED": "rejected",
    "REFUSED": "rejected",
    "GRANTED": "granted",
    "REGISTERED": "granted",
    "PUBLICATION": "pending",
    "APPLICATION": "pending",
    "REQUEST_EXAMINATION": "pending",
}


@dataclass(frozen=True)
class DerivedStatus:
    status: str
    basis_event_ids: list[str]
    reason: str


def derive_status(events: Iterable, default_status: str = "pending") -> DerivedStatus:
    """Derive current status from event history."""
    candidates: list[tuple[int, Optional[str], str, str]] = []

    for event in events:
        event_type = getattr(event, "event_type", None) or event.get("event_type")
        if not event_type:
            continue
        normalized = str(event_type).upper()
        status = EVENT_STATUS_MAP.get(normalized)
        if not status:
            continue
        priority = FINAL_STATUS_PRIORITY.get(status, 0)
        event_date = getattr(event, "event_date", None) or event.get("event_date")
        event_id = getattr(event, "id", None) or event.get("id") or ""
        candidates.append((priority, str(event_date) if event_date else "", status, str(event_id)))

    if not candidates:
        return DerivedStatus(status=default_status, basis_event_ids=[], reason="no_events")

    # Prefer higher priority, then latest date
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    priority, event_date, status, event_id = candidates[0]
    reason = f"{status} derived from {event_date or 'unknown date'} (priority={priority})"
    return DerivedStatus(status=status, basis_event_ids=[event_id] if event_id else [], reason=reason)
