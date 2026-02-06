"""Case management service for investigation cases and match candidates."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import (
    CaseMatch,
    CaseTarget,
    InvestigationCase,
    MatchCandidate,
)
from app.services.audit_service import AuditService


class CaseService:
    """Service for managing investigation cases and match candidates."""

    VALID_STATUSES = {"draft", "exploring", "reviewing", "confirmed", "archived"}
    VALID_TARGET_TYPES = {"patent", "product", "company"}
    VALID_MATCH_STATUSES = {"candidate", "reviewing", "confirmed", "dismissed"}

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # -------------------------------------------------------------------------
    # Cases
    # -------------------------------------------------------------------------

    def create_case(
        self,
        *,
        title: str,
        description: str | None = None,
        patent_id: uuid.UUID | None = None,
        assignee_id: uuid.UUID | None = None,
    ) -> InvestigationCase:
        """Create a new investigation case."""
        case = InvestigationCase(
            title=title,
            description=description,
            patent_id=patent_id,
            assignee_id=assignee_id,
        )
        self.db.add(case)
        self.db.flush()

        self.audit.log(
            action="create",
            entity_type="case",
            entity_id=case.id,
        )
        return case

    def get_case(self, case_id: uuid.UUID) -> InvestigationCase | None:
        """Get a case by ID."""
        return self.db.get(InvestigationCase, case_id)

    def list_cases(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[InvestigationCase], int]:
        """List cases with optional status filter and pagination."""
        query = self.db.query(InvestigationCase).order_by(InvestigationCase.created_at.desc())
        if status:
            query = query.filter(InvestigationCase.status == status)
        total = query.count()
        offset = (page - 1) * per_page
        cases = query.offset(offset).limit(per_page).all()
        return cases, total

    def update_case(
        self,
        case_id: uuid.UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        assignee_id: uuid.UUID | None = None,
    ) -> InvestigationCase | None:
        """Update case fields."""
        case = self.get_case(case_id)
        if not case:
            return None

        diff = {}
        if title is not None:
            diff["title"] = {"old": case.title, "new": title}
            case.title = title
        if description is not None:
            diff["description"] = {"old": case.description, "new": description}
            case.description = description
        if status is not None:
            if status not in self.VALID_STATUSES:
                msg = f"Invalid status: {status}"
                raise ValueError(msg)
            diff["status"] = {"old": case.status, "new": status}
            case.status = status
        if assignee_id is not None:
            diff["assignee_id"] = {"old": str(case.assignee_id), "new": str(assignee_id)}
            case.assignee_id = assignee_id

        case.updated_at = datetime.now(UTC)
        self.db.flush()

        if diff:
            self.audit.log(
                action="update",
                entity_type="case",
                entity_id=case.id,
                diff=diff,
            )
        return case

    # -------------------------------------------------------------------------
    # Case Targets
    # -------------------------------------------------------------------------

    def add_target(
        self,
        case_id: uuid.UUID,
        *,
        target_type: str,
        target_id: uuid.UUID,
    ) -> CaseTarget:
        """Add a target (patent/product/company) to a case."""
        if target_type not in self.VALID_TARGET_TYPES:
            msg = f"Invalid target_type: {target_type}"
            raise ValueError(msg)

        target = CaseTarget(
            case_id=case_id,
            target_type=target_type,
            target_id=target_id,
        )
        self.db.add(target)
        self.db.flush()

        self.audit.log(
            action="create",
            entity_type="case_target",
            entity_id=target.id,
            metadata={"case_id": str(case_id), "target_type": target_type},
        )
        return target

    def get_targets(self, case_id: uuid.UUID) -> list[CaseTarget]:
        """Get all targets for a case."""
        return self.db.query(CaseTarget).filter(CaseTarget.case_id == case_id).all()

    # -------------------------------------------------------------------------
    # Match Candidates
    # -------------------------------------------------------------------------

    def get_match(self, match_id: uuid.UUID) -> MatchCandidate | None:
        """Get a match candidate by ID."""
        return self.db.get(MatchCandidate, match_id)

    def list_matches(
        self,
        *,
        patent_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[MatchCandidate], int]:
        """List match candidates with filters and pagination."""
        query = self.db.query(MatchCandidate).order_by(
            MatchCandidate.score_total.desc().nullslast()
        )
        if patent_id:
            query = query.filter(MatchCandidate.patent_id == patent_id)
        if product_id:
            query = query.filter(MatchCandidate.product_id == product_id)
        if company_id:
            query = query.filter(MatchCandidate.company_id == company_id)
        if status:
            query = query.filter(MatchCandidate.status == status)
        total = query.count()
        offset = (page - 1) * per_page
        matches = query.offset(offset).limit(per_page).all()
        return matches, total

    def update_match_status(
        self,
        match_id: uuid.UUID,
        *,
        status: str,
    ) -> MatchCandidate | None:
        """Update match candidate status."""
        if status not in self.VALID_MATCH_STATUSES:
            msg = f"Invalid status: {status}"
            raise ValueError(msg)

        match = self.get_match(match_id)
        if not match:
            return None

        old_status = match.status
        match.status = status
        match.updated_at = datetime.now(UTC)
        self.db.flush()

        self.audit.log(
            action="update",
            entity_type="match_candidate",
            entity_id=match.id,
            diff={"status": {"old": old_status, "new": status}},
        )
        return match

    # -------------------------------------------------------------------------
    # Case Matches (linking cases to candidates)
    # -------------------------------------------------------------------------

    def add_case_match(
        self,
        case_id: uuid.UUID,
        match_candidate_id: uuid.UUID,
        *,
        reviewer_note: str | None = None,
    ) -> CaseMatch:
        """Link a match candidate to a case."""
        link = CaseMatch(
            case_id=case_id,
            match_candidate_id=match_candidate_id,
            reviewer_note=reviewer_note,
        )
        self.db.add(link)
        self.db.flush()
        return link

    def get_case_matches(
        self,
        case_id: uuid.UUID,
    ) -> list[CaseMatch]:
        """Get all match candidates linked to a case."""
        return self.db.query(CaseMatch).filter(CaseMatch.case_id == case_id).all()
