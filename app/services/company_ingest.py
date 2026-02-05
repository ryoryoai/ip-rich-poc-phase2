"""Company master ingestion utilities (NTA corporate number data, patent seeds)."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import (
    Company,
    CompanyFieldValue,
    Evidence,
    JpApplicant,
    JpCase,
    JpCaseApplicant,
    PatentCompanyLink,
)
from app.ingest.raw_storage import calculate_sha256
from app.services.normalization import normalize_company_name

logger = get_logger(__name__)


NTA_COLUMN_CANDIDATES: dict[str, list[str]] = {
    "corporate_number": ["法人番号", "corporate_number", "corporateNumber"],
    "name": ["商号又は名称", "名称", "name", "商号"],
    "legal_type": ["法人種別", "法人種別名", "type"],
    "address_raw": [
        "本店又は主たる事務所の所在地",
        "所在地",
        "address",
        "address_raw",
    ],
    "address_pref": ["都道府県名", "prefecture", "prefecture_name"],
    "address_city": ["市区町村名", "city", "city_name"],
    "status": ["状態", "status", "閉鎖等の区分", "処理区分"],
    "country": ["国", "country"],
}


@dataclass
class NtaIngestStats:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


def _detect_encoding(sample: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _iter_csv_rows(file_obj: io.BufferedReader, encoding: str | None = None) -> Iterable[dict]:
    sample = file_obj.read(4096)
    file_obj.seek(0)
    encoding = encoding or _detect_encoding(sample)
    text_stream = io.TextIOWrapper(file_obj, encoding=encoding, errors="replace")
    reader = csv.DictReader(text_stream)
    for row in reader:
        yield row


def _iter_rows_from_path(path: Path, encoding: str | None = None) -> Iterable[dict]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("ZIP does not contain CSV files")
            with zf.open(csv_names[0]) as csv_file:
                yield from _iter_csv_rows(csv_file, encoding=encoding)
        return

    if path.suffix.lower() == ".csv":
        with path.open("rb") as f:
            yield from _iter_csv_rows(f, encoding=encoding)
        return

    raise ValueError("Unsupported file type (expected .csv or .zip)")


def _get_first_value(row: dict, candidates: list[str]) -> str | None:
    for key in candidates:
        value = row.get(key)
        if value is None:
            continue
        value = str(value).strip()
        if value:
            return value
    return None


def _hash_value(value: str | dict | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    else:
        payload = str(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _record_company_field(
    db: Session,
    company_id: uuid.UUID,
    field_name: str,
    value: str | dict | None,
    evidence_id: uuid.UUID | None,
    source_type: str,
    source_ref: str | None,
    confidence: float | None,
    captured_at: datetime | None,
) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return

    value_hash = _hash_value(value)
    if value_hash:
        existing = (
            db.query(CompanyFieldValue)
            .filter(
                CompanyFieldValue.company_id == company_id,
                CompanyFieldValue.field_name == field_name,
                CompanyFieldValue.value_hash == value_hash,
            )
            .first()
        )
        if existing:
            if not existing.is_current:
                existing.is_current = True
            return

    db.execute(
        update(CompanyFieldValue)
        .where(
            CompanyFieldValue.company_id == company_id,
            CompanyFieldValue.field_name == field_name,
            CompanyFieldValue.is_current.is_(True),
        )
        .values(is_current=False)
    )

    db.add(
        CompanyFieldValue(
            company_id=company_id,
            field_name=field_name,
            value_text=value if isinstance(value, str) else None,
            value_json=value if isinstance(value, dict) else None,
            value_hash=value_hash,
            source_evidence_id=evidence_id,
            source_type=source_type,
            source_ref=source_ref,
            confidence_score=confidence,
            captured_at=captured_at,
            is_current=True,
        )
    )


def _build_evidence(
    db: Session,
    source_type: str,
    source_url: str | None,
    title: str | None,
    content_hash: str | None,
    content_type: str | None,
) -> Evidence:
    evidence = Evidence(
        url=source_url or "about:blank",
        source_type=source_type,
        title=title,
        retrieved_at=datetime.now(timezone.utc),
        captured_at=datetime.now(timezone.utc),
        content_hash=content_hash,
        content_type=content_type,
    )
    db.add(evidence)
    db.flush()
    return evidence


def ingest_nta_file(
    db: Session,
    path: Path,
    run_type: str,
    source_url: str | None = None,
    encoding: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    batch_size: int = 500,
) -> NtaIngestStats:
    """Ingest NTA corporate number CSV/ZIP into company master."""
    stats = NtaIngestStats()

    evidence = None
    if not dry_run:
        content_hash = calculate_sha256(path) if path.exists() else None
        evidence = _build_evidence(
            db=db,
            source_type="nta",
            source_url=source_url or str(path),
            title=f"NTA corporate data ({run_type})",
            content_hash=content_hash,
            content_type="text/csv",
        )

    for row in _iter_rows_from_path(path, encoding=encoding):
        stats.processed += 1
        if limit and stats.processed > limit:
            break

        corporate_number = _get_first_value(row, NTA_COLUMN_CANDIDATES["corporate_number"])
        if corporate_number:
            corporate_number = "".join(ch for ch in corporate_number if ch.isdigit())
        if not corporate_number or len(corporate_number) != 13:
            stats.skipped += 1
            continue

        name = _get_first_value(row, NTA_COLUMN_CANDIDATES["name"])
        if not name:
            stats.skipped += 1
            continue

        legal_type = _get_first_value(row, NTA_COLUMN_CANDIDATES["legal_type"])
        address_raw = _get_first_value(row, NTA_COLUMN_CANDIDATES["address_raw"])
        address_pref = _get_first_value(row, NTA_COLUMN_CANDIDATES["address_pref"])
        address_city = _get_first_value(row, NTA_COLUMN_CANDIDATES["address_city"])
        status = _get_first_value(row, NTA_COLUMN_CANDIDATES["status"])
        country = _get_first_value(row, NTA_COLUMN_CANDIDATES["country"]) or "JP"

        company = (
            db.query(Company)
            .filter(Company.corporate_number == corporate_number)
            .first()
        )
        is_new = False
        modified = False
        if not company:
            company = Company(
                name=name,
                corporate_number=corporate_number,
                country=country,
                legal_type=legal_type,
                normalized_name=normalize_company_name(name),
                address_raw=address_raw,
                address_pref=address_pref,
                address_city=address_city,
                status=status,
                identity_type="confirmed",
                identity_confidence=100,
            )
            if not dry_run:
                db.add(company)
                db.flush()
            is_new = True
            modified = True
        else:
            updated = False
            if name and company.name != name:
                company.name = name
                company.normalized_name = normalize_company_name(name)
                updated = True
            if legal_type and company.legal_type != legal_type:
                company.legal_type = legal_type
                updated = True
            if address_raw and company.address_raw != address_raw:
                company.address_raw = address_raw
                updated = True
            if address_pref and company.address_pref != address_pref:
                company.address_pref = address_pref
                updated = True
            if address_city and company.address_city != address_city:
                company.address_city = address_city
                updated = True
            if status and company.status != status:
                company.status = status
                updated = True
            if country and company.country != country:
                company.country = country
                updated = True
            if company.identity_type != "confirmed" or company.identity_confidence < 100:
                company.identity_type = "confirmed"
                company.identity_confidence = 100
                updated = True
            if updated and not dry_run:
                db.add(company)
            modified = updated

        if is_new:
            stats.created += 1
        elif modified:
            stats.updated += 1
        else:
            stats.skipped += 1

        if dry_run:
            continue

        _record_company_field(
            db,
            company_id=company.id,
            field_name="name",
            value=name,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="corporate_number",
            value=corporate_number,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="legal_type",
            value=legal_type,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="address_raw",
            value=address_raw,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="address_pref",
            value=address_pref,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="address_city",
            value=address_city,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="status",
            value=status,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )
        _record_company_field(
            db,
            company_id=company.id,
            field_name="country",
            value=country,
            evidence_id=evidence.id if evidence else None,
            source_type="nta",
            source_ref=path.name,
            confidence=100,
            captured_at=datetime.now(timezone.utc),
        )

        if stats.processed % batch_size == 0:
            db.commit()

    db.commit()
    return stats


def seed_companies_from_patents(
    db: Session,
    limit: int = 500,
    dry_run: bool = False,
) -> dict[str, int]:
    """Seed companies from JP applicants and create probabilistic links."""
    created = 0
    linked = 0
    skipped = 0

    applicants = (
        db.query(JpCaseApplicant, JpApplicant, JpCase)
        .join(JpApplicant, JpApplicant.id == JpCaseApplicant.applicant_id)
        .join(JpCase, JpCase.id == JpCaseApplicant.case_id)
        .order_by(JpCaseApplicant.created_at.desc())
        .limit(limit)
        .all()
    )

    for link, applicant, case in applicants:
        name = applicant.name_raw
        if not name:
            skipped += 1
            continue

        company = db.query(Company).filter(Company.name == name).first()
        if not company:
            normalized = normalize_company_name(name)
            company = db.query(Company).filter(Company.normalized_name == normalized).first()

        if not company:
            company = Company(
                name=name,
                normalized_name=normalize_company_name(name),
                identity_type="provisional",
                identity_confidence=60,
            )
            if not dry_run:
                db.add(company)
                db.flush()
            created += 1

        patent_ref = case.application_number_norm or case.application_number_raw
        if not patent_ref:
            skipped += 1
            continue

        existing_link = (
            db.query(PatentCompanyLink)
            .filter(
                PatentCompanyLink.company_id == company.id,
                PatentCompanyLink.patent_ref == patent_ref,
                PatentCompanyLink.role == link.role,
            )
            .first()
        )
        if existing_link:
            skipped += 1
            continue

        if not dry_run:
            db.add(
                PatentCompanyLink(
                    company_id=company.id,
                    document_id=None,
                    patent_ref=patent_ref,
                    role=link.role,
                    link_type="probabilistic",
                    confidence_score=60,
                    review_status="pending",
                    evidence_json={
                        "source": "jp_index",
                        "case_id": str(case.id),
                        "applicant_id": str(applicant.id),
                        "name_raw": name,
                    },
                )
            )
        linked += 1

    if not dry_run:
        db.commit()

    return {"created": created, "linked": linked, "skipped": skipped}


def apply_company_enrichment(
    db: Session,
    company: Company,
    fields: dict[str, object],
    source_type: str,
    source_url: str | None,
    payload: dict[str, object] | None = None,
    confidence: float | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Apply enrichment fields to company and record evidence/history."""
    updated = 0
    recorded = 0

    evidence = None
    if not dry_run:
        payload_hash = None
        if payload is not None:
            payload_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        evidence = _build_evidence(
            db=db,
            source_type=source_type,
            source_url=source_url or "about:blank",
            title=f"{source_type} enrichment",
            content_hash=payload_hash,
            content_type="application/json",
        )

    for field_name, value in fields.items():
        if value is None:
            continue

        if hasattr(company, field_name):
            current_value = getattr(company, field_name)
            if current_value != value and not dry_run:
                setattr(company, field_name, value)
                updated += 1

        if dry_run:
            recorded += 1
            continue

        _record_company_field(
            db,
            company_id=company.id,
            field_name=field_name,
            value=value if isinstance(value, (str, dict)) else str(value),
            evidence_id=evidence.id if evidence else None,
            source_type=source_type,
            source_ref=source_url,
            confidence=confidence,
            captured_at=datetime.now(timezone.utc),
        )
        recorded += 1

    if not dry_run:
        db.add(company)
        db.commit()

    return {"updated": updated, "recorded": recorded}
