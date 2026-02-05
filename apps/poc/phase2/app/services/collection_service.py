"""Collection job service for company/product ingestion pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import CollectionJob, CollectionItem

logger = get_logger(__name__)

CollectionHandler = Callable[[Session, CollectionItem], dict[str, Any]]


class CollectionService:
    """Create and run collection jobs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        job_type: str,
        items: list[dict[str, Any]],
        priority: int = 5,
    ) -> CollectionJob:
        job = CollectionJob(
            job_type=job_type,
            status="queued",
            priority=priority,
        )
        self.db.add(job)
        self.db.flush()

        for item in items:
            self.db.add(
                CollectionItem(
                    job_id=job.job_id,
                    entity_type=item.get("entity_type", "company"),
                    entity_id=item.get("entity_id"),
                    source_type=item.get("source_type"),
                    source_ref=item.get("source_ref"),
                    status="queued",
                    payload_json=item.get("payload_json"),
                )
            )

        self.db.commit()
        self.db.refresh(job)
        return job

    def run_job(self, job_id: str, handler: CollectionHandler) -> dict[str, Any]:
        job = self.db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
        if not job:
            raise ValueError("Collection job not found")

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()

        results: list[dict[str, Any]] = []
        failed = 0

        for item in job.items:
            item.status = "running"
            item.started_at = datetime.now(timezone.utc)
            self.db.commit()

            try:
                result = handler(self.db, item)
                item.status = result.get("status", "succeeded")
                item.payload_json = result
            except Exception as exc:  # noqa: BLE001
                failed += 1
                item.status = "failed"
                item.error_code = "handler_error"
                item.error_detail = str(exc)
                logger.exception("Collection item failed", item_id=item.item_id)
            finally:
                item.finished_at = datetime.now(timezone.utc)
                self.db.commit()

            results.append(
                {
                    "item_id": str(item.item_id),
                    "status": item.status,
                    "error_code": item.error_code,
                    "error_detail": item.error_detail,
                }
            )

        job.finished_at = datetime.now(timezone.utc)
        job.status = "completed" if failed == 0 else "partial"
        self.db.commit()

        return {
            "job_id": str(job.job_id),
            "status": job.status,
            "failed": failed,
            "results": results,
        }
