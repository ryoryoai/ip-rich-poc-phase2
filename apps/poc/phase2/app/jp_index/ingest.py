"""Ingestion pipeline for JP Patent Index (normalized JSONL)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, TypedDict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import (
    JpIngestBatch,
    JpIngestBatchFile,
    JpCase,
    JpDocument,
    JpNumberAlias,
    JpApplicant,
    JpCaseApplicant,
    JpClassification,
    JpStatusEvent,
    JpStatusSnapshot,
    JpSearchDocument,
)
from app.db.session import engine
from app.jp_index.normalize import normalize_number, normalize_applicant_name
from app.jp_index.status import derive_status

logger = get_logger(__name__)


class NormalizedDocument(TypedDict, total=False):
    doc_type: str
    publication_number: str
    patent_number: str
    kind: str
    publication_date: str


class NormalizedApplicant(TypedDict, total=False):
    name_raw: str
    name_norm: str
    role: str
    is_primary: bool
    normalize_confidence: float
    source: str


class NormalizedClassification(TypedDict, total=False):
    type: str
    code: str
    version: str
    is_primary: bool


class NormalizedStatusEvent(TypedDict, total=False):
    event_type: str
    event_date: str
    source: str
    payload: dict[str, Any]


class NormalizedRecord(TypedDict, total=False):
    application_number: str
    filing_date: str
    title: str
    abstract: str
    last_update_date: str
    documents: list[NormalizedDocument]
    applicants: list[NormalizedApplicant]
    classifications: list[NormalizedClassification]
    status_events: list[NormalizedStatusEvent]


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def create_ingest_batch(
    db: Session,
    source: str,
    run_type: str,
    update_date: Optional[date],
    batch_key: str,
    metadata: Optional[dict[str, Any]] = None,
) -> JpIngestBatch:
    existing = db.query(JpIngestBatch).filter(JpIngestBatch.batch_key == batch_key).first()
    if existing:
        return existing
    batch = JpIngestBatch(
        source=source,
        run_type=run_type,
        update_date=update_date,
        batch_key=batch_key,
        status="running",
        started_at=datetime.now(timezone.utc),
        metadata_json=metadata or {},
    )
    db.add(batch)
    db.flush()
    return batch


def register_batch_file(
    db: Session,
    batch: JpIngestBatch,
    raw_file_id: Optional[str],
    file_sha256: Optional[str],
    original_name: Optional[str],
) -> None:
    link = JpIngestBatchFile(
        batch_id=batch.id,
        raw_file_id=raw_file_id,
        file_sha256=file_sha256,
        original_name=original_name,
    )
    db.add(link)


def ingest_normalized_jsonl(
    db: Session,
    path: Path,
    batch: JpIngestBatch,
    source: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Ingest normalized JSONL into JP Patent Index tables."""
    if not path.exists():
        raise FileNotFoundError(f"Normalized file not found: {path}")

    counters = {"records": 0, "created": 0, "updated": 0, "errors": 0}
    is_postgres = engine.dialect.name == "postgresql"

    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            counters["records"] += 1
            try:
                record = json.loads(line)
                _upsert_record(db, record, source, is_postgres)
                counters["updated"] += 1
            except Exception as exc:
                counters["errors"] += 1
                logger.exception("Failed to ingest record", line_no=line_no, error=str(exc))

    batch.status = "completed" if counters["errors"] == 0 else "partial"
    batch.finished_at = datetime.now(timezone.utc)
    batch.counts_json = counters

    if dry_run:
        db.rollback()
    return counters


def _upsert_record(
    db: Session,
    record: dict[str, Any],
    source: str,
    is_postgres: bool,
) -> None:
    case_data = record.get("case") or record
    documents = record.get("documents") or case_data.get("documents") or []
    applicants = record.get("applicants") or case_data.get("applicants") or []
    classifications = record.get("classifications") or case_data.get("classifications") or []
    status_events = record.get("status_events") or case_data.get("status_events") or []

    application_number = case_data.get("application_number") or case_data.get("application_number_raw")
    filing_date = parse_date(case_data.get("filing_date"))
    title = case_data.get("title")
    abstract = case_data.get("abstract")
    last_update_date = parse_date(case_data.get("last_update_date"))

    numbers: list = []
    app_norm = normalize_number(application_number, number_type_hint="application")
    if app_norm:
        numbers.append(app_norm)

    case = None
    if app_norm and app_norm.number_norm:
        case = (
            db.query(JpCase)
            .filter(JpCase.application_number_norm == app_norm.number_norm)
            .first()
        )

    if not case:
        for num in numbers:
            alias = (
                db.query(JpNumberAlias)
                .filter(
                    JpNumberAlias.number_type == num.number_type,
                    JpNumberAlias.number_norm == num.number_norm,
                )
                .first()
            )
            if alias:
                case = db.query(JpCase).filter(JpCase.id == alias.case_id).first()
                break

    if not case:
        case = JpCase(
            country="JP",
            application_number_raw=application_number,
            application_number_norm=app_norm.number_norm if app_norm else None,
            filing_date=filing_date,
            title=title,
            abstract=abstract,
            last_update_date=last_update_date,
        )
        db.add(case)
        db.flush()
    else:
        if application_number and not case.application_number_raw:
            case.application_number_raw = application_number
        if app_norm and not case.application_number_norm:
            case.application_number_norm = app_norm.number_norm
        if filing_date and not case.filing_date:
            case.filing_date = filing_date
        if title and not case.title:
            case.title = title
        if abstract and not case.abstract:
            case.abstract = abstract
        if last_update_date:
            if not case.last_update_date or last_update_date > case.last_update_date:
                case.last_update_date = last_update_date

    _upsert_numbers(db, case, app_norm)
    _upsert_documents(db, case, documents)
    _upsert_applicants(db, case, applicants)
    _upsert_classifications(db, case, classifications)
    _upsert_status_events(db, case, status_events, source)
    _update_status_snapshot(db, case)
    _upsert_search_document(db, case, is_postgres)


def _upsert_numbers(db: Session, case: JpCase, app_norm) -> None:
    if not app_norm:
        return
    existing = (
        db.query(JpNumberAlias)
        .filter(
            JpNumberAlias.number_type == app_norm.number_type,
            JpNumberAlias.number_norm == app_norm.number_norm,
        )
        .first()
    )
    if existing:
        if existing.case_id != case.id:
            existing.case_id = case.id
        return
    alias = JpNumberAlias(
        case_id=case.id,
        number_type=app_norm.number_type,
        number_raw=app_norm.raw,
        number_norm=app_norm.number_norm,
        country=app_norm.country,
        kind=app_norm.kind,
        is_primary=True,
    )
    db.add(alias)


def _upsert_documents(db: Session, case: JpCase, documents: list[dict[str, Any]]) -> None:
    for doc in documents:
        doc_type = doc.get("doc_type") or "publication"
        pub_number = doc.get("publication_number")
        patent_number = doc.get("patent_number")
        kind = doc.get("kind")
        pub_date = parse_date(doc.get("publication_date"))

        pub_norm = normalize_number(pub_number, number_type_hint="publication") if pub_number else None
        pat_norm = normalize_number(patent_number, number_type_hint="patent") if patent_number else None

        existing = None
        if pub_norm:
            existing = (
                db.query(JpDocument)
                .filter(JpDocument.publication_number_norm == pub_norm.number_norm)
                .first()
            )
        if not existing and pat_norm:
            existing = (
                db.query(JpDocument)
                .filter(JpDocument.patent_number_norm == pat_norm.number_norm)
                .first()
            )

        if not existing:
            existing = JpDocument(
                case_id=case.id,
                doc_type=doc_type,
                publication_number_raw=pub_number,
                publication_number_norm=pub_norm.number_norm if pub_norm else None,
                patent_number_raw=patent_number,
                patent_number_norm=pat_norm.number_norm if pat_norm else None,
                kind=kind or (pub_norm.kind if pub_norm else pat_norm.kind if pat_norm else None),
                publication_date=pub_date,
            )
            db.add(existing)
            db.flush()
        else:
            if existing.case_id != case.id:
                existing.case_id = case.id
            if pub_number and not existing.publication_number_raw:
                existing.publication_number_raw = pub_number
            if pub_norm and not existing.publication_number_norm:
                existing.publication_number_norm = pub_norm.number_norm
            if patent_number and not existing.patent_number_raw:
                existing.patent_number_raw = patent_number
            if pat_norm and not existing.patent_number_norm:
                existing.patent_number_norm = pat_norm.number_norm
            if kind and not existing.kind:
                existing.kind = kind
            if pub_date and not existing.publication_date:
                existing.publication_date = pub_date

        if pub_norm:
            _ensure_alias(db, case.id, existing.id, pub_norm, is_primary=False)
        if pat_norm:
            _ensure_alias(db, case.id, existing.id, pat_norm, is_primary=False)


def _ensure_alias(db: Session, case_id: str, document_id: str, norm, is_primary: bool) -> None:
    existing = (
        db.query(JpNumberAlias)
        .filter(
            JpNumberAlias.number_type == norm.number_type,
            JpNumberAlias.number_norm == norm.number_norm,
        )
        .first()
    )
    if existing:
        if document_id and not existing.document_id:
            existing.document_id = document_id
        if case_id and existing.case_id != case_id:
            existing.case_id = case_id
        return
    alias = JpNumberAlias(
        case_id=case_id,
        document_id=document_id,
        number_type=norm.number_type,
        number_raw=norm.raw,
        number_norm=norm.number_norm,
        country=norm.country,
        kind=norm.kind,
        is_primary=is_primary,
    )
    db.add(alias)


def _upsert_applicants(db: Session, case: JpCase, applicants: list[dict[str, Any]]) -> None:
    for app in applicants:
        name_raw = app.get("name_raw") or app.get("name")
        if not name_raw:
            continue
        name_norm = app.get("name_norm") or normalize_applicant_name(name_raw)
        existing = (
            db.query(JpApplicant)
            .filter(JpApplicant.name_norm == name_norm)
            .first()
        )
        if not existing:
            existing = JpApplicant(
                name_raw=name_raw,
                name_norm=name_norm,
                normalize_confidence=app.get("normalize_confidence"),
                source=app.get("source"),
            )
            db.add(existing)
            db.flush()

        link = (
            db.query(JpCaseApplicant)
            .filter(
                JpCaseApplicant.case_id == case.id,
                JpCaseApplicant.applicant_id == existing.id,
                JpCaseApplicant.role == (app.get("role") or "applicant"),
            )
            .first()
        )
        if not link:
            db.add(
                JpCaseApplicant(
                    case_id=case.id,
                    applicant_id=existing.id,
                    role=app.get("role") or "applicant",
                    is_primary=bool(app.get("is_primary", False)),
                )
            )


def _upsert_classifications(db: Session, case: JpCase, classifications: list[dict[str, Any]]) -> None:
    for cls in classifications:
        code = cls.get("code")
        cls_type = cls.get("type")
        if not code or not cls_type:
            continue
        existing = (
            db.query(JpClassification)
            .filter(
                JpClassification.case_id == case.id,
                JpClassification.type == cls_type,
                JpClassification.code == code,
            )
            .first()
        )
        if existing:
            continue
        db.add(
            JpClassification(
                case_id=case.id,
                type=cls_type,
                code=code,
                version=cls.get("version"),
                is_primary=bool(cls.get("is_primary", False)),
            )
        )


def _upsert_status_events(
    db: Session,
    case: JpCase,
    events: list[dict[str, Any]],
    source: str,
) -> None:
    for ev in events:
        event_type = ev.get("event_type")
        if not event_type:
            continue
        event_date = parse_date(ev.get("event_date"))
        existing = (
            db.query(JpStatusEvent)
            .filter(
                JpStatusEvent.case_id == case.id,
                JpStatusEvent.event_type == event_type,
                JpStatusEvent.event_date == event_date,
                JpStatusEvent.source == (ev.get("source") or source),
            )
            .first()
        )
        if existing:
            continue
        db.add(
            JpStatusEvent(
                case_id=case.id,
                event_type=event_type,
                event_date=event_date,
                source=ev.get("source") or source,
                payload_json=ev.get("payload"),
            )
        )


def _update_status_snapshot(db: Session, case: JpCase) -> None:
    events = db.query(JpStatusEvent).filter(JpStatusEvent.case_id == case.id).all()
    derived = derive_status(events)

    if case.current_status != derived.status:
        case.current_status = derived.status
        case.status_updated_at = datetime.now(timezone.utc)

    snapshot = JpStatusSnapshot(
        case_id=case.id,
        status=derived.status,
        logic_version="v1",
        basis_event_ids={"event_ids": derived.basis_event_ids},
        reason=derived.reason,
    )
    db.add(snapshot)


def _upsert_search_document(db: Session, case: JpCase, is_postgres: bool) -> None:
    applicants = (
        db.query(JpApplicant.name_raw)
        .join(JpCaseApplicant, JpCaseApplicant.applicant_id == JpApplicant.id)
        .filter(JpCaseApplicant.case_id == case.id)
        .all()
    )
    applicant_text = " ".join(a[0] for a in applicants if a[0])

    classifications = (
        db.query(JpClassification.code)
        .filter(JpClassification.case_id == case.id)
        .all()
    )
    classification_text = " ".join(c[0] for c in classifications if c[0])

    search_doc = db.query(JpSearchDocument).filter(JpSearchDocument.case_id == case.id).first()
    if not search_doc:
        search_doc = JpSearchDocument(case_id=case.id)
        db.add(search_doc)

    search_doc.title = case.title
    search_doc.abstract = case.abstract
    search_doc.applicants_text = applicant_text
    search_doc.classifications_text = classification_text
    search_doc.status = case.current_status
    search_doc.publication_date = case.last_update_date

    combined_text = " ".join(filter(None, [case.title, case.abstract, applicant_text, classification_text]))
    if is_postgres:
        search_doc.tsv = func.to_tsvector("simple", combined_text)
    else:
        search_doc.tsv = combined_text
