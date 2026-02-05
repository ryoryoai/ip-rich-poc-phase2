"""Search adapter for JP Patent Index."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.db.models import JpCase, JpSearchDocument, JpNumberAlias
from app.db.session import engine
from app.jp_index.normalize import normalize_number


@dataclass
class SearchParams:
    q: Optional[str] = None
    number: Optional[str] = None
    applicant: Optional[str] = None
    classification: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    page: int = 1
    page_size: int = 20
    sort: str = "updated_desc"


class PostgresSearchAdapter:
    """Search adapter using Postgres FTS when available."""

    def search(self, db: Session, params: SearchParams) -> dict[str, Any]:
        if params.number:
            return self._search_by_number(db, params.number)

        query = (
            db.query(JpCase)
            .outerjoin(JpSearchDocument, JpSearchDocument.case_id == JpCase.id)
            .options(selectinload(JpCase.number_aliases), selectinload(JpCase.documents))
        )

        if params.status:
            query = query.filter(JpCase.current_status == params.status)
        if params.from_date:
            query = query.filter(JpCase.last_update_date >= params.from_date)
        if params.to_date:
            query = query.filter(JpCase.last_update_date <= params.to_date)
        if params.applicant:
            query = query.filter(JpSearchDocument.applicants_text.ilike(f"%{params.applicant}%"))
        if params.classification:
            query = query.filter(JpSearchDocument.classifications_text.ilike(f"%{params.classification}%"))

        is_postgres = engine.dialect.name == "postgresql"
        if params.q:
            if is_postgres:
                ts_query = func.plainto_tsquery("simple", params.q)
                query = query.filter(JpSearchDocument.tsv.op("@@")(ts_query))
                if params.sort == "relevance":
                    query = query.order_by(func.ts_rank(JpSearchDocument.tsv, ts_query).desc())
            else:
                query = query.filter(
                    JpSearchDocument.title.ilike(f"%{params.q}%")
                    | JpSearchDocument.abstract.ilike(f"%{params.q}%")
                )

        if params.sort == "updated_desc":
            query = query.order_by(JpCase.last_update_date.desc().nullslast())
        elif params.sort == "updated_asc":
            query = query.order_by(JpCase.last_update_date.asc().nullslast())

        total = query.count()

        page = max(params.page, 1)
        page_size = min(max(params.page_size, 1), 200)
        cases = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._case_to_summary(case) for case in cases],
        }

    def _search_by_number(self, db: Session, number: str) -> dict[str, Any]:
        normalized = normalize_number(number)
        if not normalized:
            return {"total": 0, "page": 1, "page_size": 20, "items": []}

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

        if not alias:
            return {"total": 0, "page": 1, "page_size": 20, "items": []}

        case = (
            db.query(JpCase)
            .options(selectinload(JpCase.number_aliases))
            .filter(JpCase.id == alias.case_id)
            .first()
        )
        if not case:
            return {"total": 0, "page": 1, "page_size": 20, "items": []}

        return {
            "total": 1,
            "page": 1,
            "page_size": 1,
            "items": [self._case_to_summary(case)],
        }

    def _case_to_summary(self, case: JpCase) -> dict[str, Any]:
        registration_date = None
        patent_numbers: list[str] = []
        for doc in (case.documents or []):
            if doc.patent_number_norm:
                patent_numbers.append(doc.patent_number_norm)
            if doc.doc_type == "registration" and doc.publication_date:
                if not registration_date or doc.publication_date > registration_date:
                    registration_date = doc.publication_date

        numbers = [
            {
                "type": alias.number_type,
                "number": alias.number_norm,
                "is_primary": alias.is_primary,
            }
            for alias in (case.number_aliases or [])
        ]
        return {
            "case_id": str(case.id),
            "application_number": case.application_number_norm,
            "title": case.title,
            "status": case.current_status,
            "rights_status": self._derive_rights_status(case.current_status),
            "registration_date": registration_date.isoformat() if registration_date else None,
            "patent_numbers": patent_numbers,
            "last_update_date": case.last_update_date.isoformat() if case.last_update_date else None,
            "numbers": numbers,
        }

    def _derive_rights_status(self, status: Optional[str]) -> Optional[str]:
        if not status:
            return None
        normalized = status.lower()
        if normalized in {"expired", "withdrawn", "abandoned", "rejected"}:
            return "expired"
        if normalized in {"granted", "pending"}:
            return "active"
        return "unknown"
