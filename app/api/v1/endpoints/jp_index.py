"""JP Patent Index endpoints."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import get_logger
from app.jp_index.audit import record_audit_log
from app.jp_index.cache import changes_cache, resolve_cache, search_cache
from app.jp_index.rate_limit import rate_limiter, rate_limit_key
from app.core import settings
from app.db.models import (
    JpCase,
    JpDocument,
    JpNumberAlias,
    JpApplicant,
    JpCaseApplicant,
    JpClassification,
    JpStatusEvent,
    JpStatusSnapshot,
    JpIngestBatch,
)
from app.jp_index.normalize import normalize_number
from app.jp_index.search import PostgresSearchAdapter, SearchParams

router = APIRouter()
logger = get_logger(__name__)


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


class ExportRequest(BaseModel):
    q: Optional[str] = None
    number: Optional[str] = None
    applicant: Optional[str] = None
    classification: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    sort: str = "updated_desc"
    limit: int = Field(1000, ge=1, le=100000)
    format: str = Field("json", pattern="^(json|csv)$")


@router.get("/search")
def search_patents(
    request: Request,
    q: Annotated[Optional[str], Query()] = None,
    number: Annotated[Optional[str], Query()] = None,
    applicant: Annotated[Optional[str], Query()] = None,
    classification: Annotated[Optional[str], Query()] = None,
    status: Annotated[Optional[str], Query()] = None,
    from_date: Annotated[Optional[date], Query()] = None,
    to_date: Annotated[Optional[date], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 20,
    sort: Annotated[str, Query()] = "updated_desc",
    db: Annotated[Session, Depends(get_db)] = None,
):
    client_ip = _client_ip(request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_search")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    params = SearchParams(
        q=q,
        number=number,
        applicant=applicant,
        classification=classification,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    adapter = PostgresSearchAdapter()

    cache_key = json.dumps(
        {
            "q": q,
            "number": number,
            "applicant": applicant,
            "classification": classification,
            "status": status,
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
            "page": page,
            "page_size": page_size,
            "sort": sort,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    cached = search_cache.get(cache_key)
    if cached is not None:
        record_audit_log(
            request,
            action="jp_index_search",
            payload={"cache": "hit", "filters": json.loads(cache_key)},
        )
        return cached

    result = adapter.search(db, params)
    search_cache.set(cache_key, result)
    record_audit_log(
        request,
        action="jp_index_search",
        payload={"cache": "miss", "filters": json.loads(cache_key)},
    )
    return result


@router.get("/resolve")
def resolve_number(
    request: Request,
    input: Annotated[str, Query(description="Patent number in various formats")],
    db: Annotated[Session, Depends(get_db)],
):
    client_ip = _client_ip(request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_resolve")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    cache_key = input.strip()
    cached = resolve_cache.get(cache_key)
    if cached is not None:
        record_audit_log(
            request,
            action="jp_index_resolve",
            payload={"input": input, "cache": "hit"},
            resource_id=cached.get("case_id"),
        )
        return cached

    normalized = normalize_number(input)
    if not normalized:
        raise HTTPException(status_code=400, detail=f"Cannot parse number: {input}")

    alias = (
        db.query(JpNumberAlias)
        .filter(
            JpNumberAlias.number_type == normalized.number_type,
            JpNumberAlias.number_norm == normalized.number_norm,
        )
        .first()
    )
    if not alias and normalized.number_base:
        alias = (
            db.query(JpNumberAlias)
            .filter(
                JpNumberAlias.number_type == normalized.number_type,
                JpNumberAlias.number_norm.like(f"{normalized.number_base}%"),
            )
            .first()
        )

    response = {
        "input": input,
        "normalized": normalized.number_norm,
        "number_type": normalized.number_type,
        "case_id": str(alias.case_id) if alias else None,
    }
    resolve_cache.set(cache_key, response)
    record_audit_log(
        request,
        action="jp_index_resolve",
        payload={"input": input, "normalized": normalized.number_norm, "cache": "miss"},
        resource_id=response.get("case_id"),
    )
    return response


@router.get("/patents/{case_id}")
def get_case_detail(
    request: Request,
    case_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    client_ip = _client_ip(request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_detail")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid case_id") from exc

    case = db.query(JpCase).filter(JpCase.id == case_uuid).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    numbers = (
        db.query(JpNumberAlias)
        .filter(JpNumberAlias.case_id == case.id)
        .all()
    )
    documents = (
        db.query(JpDocument)
        .filter(JpDocument.case_id == case.id)
        .all()
    )
    registration_date = None
    patent_numbers = []
    for doc in documents:
        if doc.patent_number_norm:
            patent_numbers.append(doc.patent_number_norm)
        if doc.doc_type == "registration" and doc.publication_date:
            if not registration_date or doc.publication_date > registration_date:
                registration_date = doc.publication_date
    applicants = (
        db.query(JpApplicant, JpCaseApplicant)
        .join(JpCaseApplicant, JpCaseApplicant.applicant_id == JpApplicant.id)
        .filter(JpCaseApplicant.case_id == case.id)
        .all()
    )
    classifications = (
        db.query(JpClassification)
        .filter(JpClassification.case_id == case.id)
        .all()
    )
    events = (
        db.query(JpStatusEvent)
        .filter(JpStatusEvent.case_id == case.id)
        .order_by(JpStatusEvent.event_date.asc().nullslast())
        .all()
    )
    has_renewal = any(
        e.event_type
        and any(token in e.event_type.upper() for token in ["RENEW", "MAINTENANCE", "FEE_PAID"])
        for e in events
    )
    snapshots = (
        db.query(JpStatusSnapshot)
        .filter(JpStatusSnapshot.case_id == case.id)
        .order_by(JpStatusSnapshot.derived_at.desc())
        .all()
    )

    record_audit_log(
        request,
        action="jp_index_case_detail",
        payload={"case_id": case_id},
        resource_id=case_id,
    )
    return {
        "case": {
            "case_id": str(case.id),
            "application_number_raw": case.application_number_raw,
            "application_number_norm": case.application_number_norm,
            "filing_date": case.filing_date.isoformat() if case.filing_date else None,
            "title": case.title,
            "abstract": case.abstract,
            "current_status": case.current_status,
            "rights_status": (
                "expired"
                if case.current_status in {"expired", "withdrawn", "abandoned", "rejected"}
                else "renewed"
                if has_renewal
                else "active"
                if case.current_status
                else None
            ),
            "status_updated_at": case.status_updated_at.isoformat() if case.status_updated_at else None,
            "last_update_date": case.last_update_date.isoformat() if case.last_update_date else None,
            "registration_date": registration_date.isoformat() if registration_date else None,
            "patent_numbers": patent_numbers,
        },
        "numbers": [
            {
                "type": n.number_type,
                "number_raw": n.number_raw,
                "number_norm": n.number_norm,
                "kind": n.kind,
                "is_primary": n.is_primary,
            }
            for n in numbers
        ],
        "documents": [
            {
                "doc_type": d.doc_type,
                "publication_number_raw": d.publication_number_raw,
                "publication_number_norm": d.publication_number_norm,
                "patent_number_raw": d.patent_number_raw,
                "patent_number_norm": d.patent_number_norm,
                "kind": d.kind,
                "publication_date": d.publication_date.isoformat() if d.publication_date else None,
            }
            for d in documents
        ],
        "applicants": [
            {
                "name_raw": app.name_raw,
                "name_norm": app.name_norm,
                "role": link.role,
                "is_primary": link.is_primary,
            }
            for app, link in applicants
        ],
        "classifications": [
            {
                "type": c.type,
                "code": c.code,
                "version": c.version,
                "is_primary": c.is_primary,
            }
            for c in classifications
        ],
        "status_events": [
            {
                "event_type": e.event_type,
                "event_date": e.event_date.isoformat() if e.event_date else None,
                "source": e.source,
            }
            for e in events
        ],
        "status_snapshots": [
            {
                "status": s.status,
                "derived_at": s.derived_at.isoformat() if s.derived_at else None,
                "logic_version": s.logic_version,
                "reason": s.reason,
            }
            for s in snapshots
        ],
    }


@router.get("/changes")
def get_changes(
    request: Request,
    from_date: Annotated[date, Query(description="YYYY-MM-DD")],
    db: Annotated[Session, Depends(get_db)],
):
    client_ip = _client_ip(request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_changes")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    cache_key = from_date.isoformat()
    cached = changes_cache.get(cache_key)
    if cached is not None:
        record_audit_log(
            request,
            action="jp_index_changes",
            payload={"from_date": cache_key, "cache": "hit"},
        )
        return cached

    cases = (
        db.query(JpCase)
        .filter(JpCase.last_update_date >= from_date)
        .order_by(JpCase.last_update_date.desc())
        .all()
    )
    response = {
        "from_date": from_date.isoformat(),
        "count": len(cases),
        "items": [
            {
                "case_id": str(case.id),
                "application_number": case.application_number_norm,
                "title": case.title,
                "status": case.current_status,
                "last_update_date": case.last_update_date.isoformat() if case.last_update_date else None,
            }
            for case in cases
        ],
    }
    changes_cache.set(cache_key, response)
    record_audit_log(
        request,
        action="jp_index_changes",
        payload={"from_date": cache_key, "count": len(cases), "cache": "miss"},
    )
    return response


@router.post("/export")
def export_patents(
    http_request: Request,
    payload: ExportRequest,
    db: Annotated[Session, Depends(get_db)],
    export_token: Annotated[Optional[str], Header(alias="X-Export-Token")] = None,
):
    client_ip = _client_ip(http_request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_export")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if not settings.jp_index_export_enabled:
        raise HTTPException(status_code=403, detail="Export is disabled")
    if payload.limit > settings.jp_index_export_max:
        raise HTTPException(
            status_code=400,
            detail=f"Export limit exceeds max {settings.jp_index_export_max}",
        )
    if settings.jp_index_export_token:
        if not export_token or export_token != settings.jp_index_export_token:
            raise HTTPException(status_code=401, detail="Invalid export token")

    params = SearchParams(
        q=payload.q,
        number=payload.number,
        applicant=payload.applicant,
        classification=payload.classification,
        status=payload.status,
        from_date=payload.from_date,
        to_date=payload.to_date,
        page=1,
        page_size=payload.limit,
        sort=payload.sort,
    )
    adapter = PostgresSearchAdapter()
    record_audit_log(
        http_request,
        action="jp_index_export",
        payload={
            "format": payload.format,
            "limit": payload.limit,
            "q": payload.q,
            "number": payload.number,
            "applicant": payload.applicant,
            "classification": payload.classification,
            "status": payload.status,
            "from_date": str(payload.from_date) if payload.from_date else None,
            "to_date": str(payload.to_date) if payload.to_date else None,
        },
    )
    result = adapter.search(db, params)

    if payload.format == "json":
        return result

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["case_id", "application_number", "title", "status", "last_update_date"])
    for item in result["items"]:
        writer.writerow([
            item.get("case_id"),
            item.get("application_number"),
            item.get("title"),
            item.get("status"),
            item.get("last_update_date"),
        ])
    return PlainTextResponse(output.getvalue(), media_type="text/csv")


@router.get("/ingest/runs")
def list_ingest_runs(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Annotated[Session, Depends(get_db)] = None,
):
    client_ip = _client_ip(request)
    if not rate_limiter.check(rate_limit_key(client_ip, "jp_index_ingest_runs")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    runs = (
        db.query(JpIngestBatch)
        .order_by(JpIngestBatch.started_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    record_audit_log(
        request,
        action="jp_index_ingest_runs",
        payload={"limit": limit, "count": len(runs)},
    )
    return {
        "items": [
            {
                "batch_id": str(run.id),
                "source": run.source,
                "run_type": run.run_type,
                "update_date": run.update_date.isoformat() if run.update_date else None,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "counts": run.counts_json,
            }
            for run in runs
        ]
    }
