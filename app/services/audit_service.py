"""Audit logging service for tracking entity operations."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import AuditLog


class AuditService:
    """Service for creating audit log entries."""

    def __init__(self, db: Session, tenant_id: uuid.UUID | None = None):
        self.db = db
        self.tenant_id = tenant_id or uuid.UUID("a0000000-0000-0000-0000-000000000001")

    def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        diff: dict | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        """Create an audit log entry.

        Args:
            action: Operation type ('create', 'update', 'delete', 'export',
                    'approve', 'reject').
            entity_type: Entity being acted on ('case', 'evidence',
                         'match_candidate', 'claim_chart', 'report').
            entity_id: UUID of the entity.
            actor_id: UUID of the user performing the action.
            diff: JSON diff of changes (for updates).
            metadata: Additional metadata.

        Returns:
            The created AuditLog record.
        """
        entry = AuditLog(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            diff=diff,
            metadata_json=metadata or {},
        )
        self.db.add(entry)
        return entry
