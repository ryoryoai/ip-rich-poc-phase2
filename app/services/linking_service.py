"""Linking utilities for patent/company/product relationships."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import Company, JpApplicant, JpCaseApplicant, JpCase, PatentCompanyLink
from app.services.normalization import normalize_company_name

logger = get_logger(__name__)


def link_patents_by_name(
    db: Session,
    limit: int = 1000,
    dry_run: bool = False,
) -> dict[str, int]:
    """Link JP applicants to companies using name matching."""
    linked = 0
    skipped = 0

    rows = (
        db.query(JpCaseApplicant, JpApplicant, JpCase)
        .join(JpApplicant, JpApplicant.id == JpCaseApplicant.applicant_id)
        .join(JpCase, JpCase.id == JpCaseApplicant.case_id)
        .order_by(JpCaseApplicant.created_at.desc())
        .limit(limit)
        .all()
    )

    for link, applicant, case in rows:
        name_raw = applicant.name_raw
        if not name_raw:
            skipped += 1
            continue

        normalized = applicant.name_norm or normalize_company_name(name_raw)
        company = (
            db.query(Company)
            .filter(Company.normalized_name == normalized)
            .first()
        )
        if not company:
            skipped += 1
            continue

        patent_ref = case.application_number_norm or case.application_number_raw
        if not patent_ref:
            skipped += 1
            continue

        existing = (
            db.query(PatentCompanyLink)
            .filter(
                PatentCompanyLink.company_id == company.id,
                PatentCompanyLink.patent_ref == patent_ref,
                PatentCompanyLink.role == link.role,
            )
            .first()
        )
        if existing:
            skipped += 1
            continue

        deterministic = company.identity_type == "confirmed" and company.name == name_raw
        link_type = "deterministic" if deterministic else "probabilistic"
        confidence = 95 if deterministic else 70
        review_status = "approved" if deterministic else "pending"

        if not dry_run:
            db.add(
                PatentCompanyLink(
                    company_id=company.id,
                    document_id=None,
                    patent_ref=patent_ref,
                    role=link.role,
                    link_type=link_type,
                    confidence_score=confidence,
                    review_status=review_status,
                    evidence_json={
                        "source": "jp_index",
                        "case_id": str(case.id),
                        "applicant_id": str(applicant.id),
                        "name_raw": name_raw,
                    },
                )
            )
        linked += 1

    if not dry_run:
        db.commit()

    return {"linked": linked, "skipped": skipped}
