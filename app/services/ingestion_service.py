"""Ingestion service for patent raw file acquisition jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import IngestionJob, IngestionJobItem
import base64

from app.core import settings
from app.ingest.raw_storage import ingest_single_file, ingest_bytes
from app.services.jpo_api_client import JpoApiClient

logger = get_logger(__name__)


class IngestionService:
    """Service for managing ingestion jobs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        items: Iterable[dict],
        priority: int = 5,
        force_refresh: bool = False,
        source_preference: str | None = None,
        idempotency_key: str | None = None,
    ) -> IngestionJob:
        """Create a new ingestion job with queued items."""
        if idempotency_key:
            existing = (
                self.db.query(IngestionJob)
                .filter(IngestionJob.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                return existing

        job = IngestionJob(
            status="queued",
            priority=priority,
            force_refresh=force_refresh,
            source_preference=source_preference,
            idempotency_key=idempotency_key,
        )
        self.db.add(job)
        self.db.flush()

        for item in items:
            self.db.add(
                IngestionJobItem(
                    job_id=job.job_id,
                    input_number=item["input_number"],
                    input_number_type=item["input_number_type"],
                    status="queued",
                    target_version_hint=item.get("target_version_hint"),
                )
            )

        self.db.commit()
        self.db.refresh(job)
        return job

    def run_job(
        self,
        job_id: str,
        storage: str = "supabase",
        bucket: str | None = None,
    ) -> dict:
        """Run an ingestion job. Currently supports local_path hints only."""
        job = (
            self.db.query(IngestionJob)
            .filter(IngestionJob.job_id == job_id)
            .first()
        )
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()

        succeeded = 0
        skipped = 0
        failed = 0

        for item in job.items:
            if item.status in {"succeeded", "skipped"} and not job.force_refresh:
                continue

            item.status = "running"
            self.db.commit()

            result = self._process_item(item, storage, bucket)
            status = result["status"]
            if status in {"ingested", "skipped"}:
                item.status = "succeeded" if status == "ingested" else "skipped"
                succeeded += 1 if status == "ingested" else 0
                skipped += 1 if status == "skipped" else 0
            else:
                item.status = "failed"
                item.error_code = result.get("error_code")
                item.error_detail = result.get("error_detail")
                item.retry_count += 1
                failed += 1

            self.db.commit()

        job.finished_at = datetime.now(timezone.utc)
        if failed == 0 and skipped == 0:
            job.status = "succeeded"
        elif failed == 0:
            job.status = "partial"
        elif succeeded == 0:
            job.status = "failed"
            job.error_code = "INGEST_FAILED"
            job.error_detail = "All items failed"
        else:
            job.status = "partial"

        self.db.commit()

        return {
            "job_id": str(job.job_id),
            "status": job.status,
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
        }

    def _process_item(
        self,
        item: IngestionJobItem,
        storage: str,
        bucket: str | None,
    ) -> dict:
        hint = item.target_version_hint or {}
        local_path = hint.get("local_path")
        bulk_rel_path = hint.get("bulk_rel_path") or hint.get("bulk_path")
        raw_base64 = hint.get("raw_base64") or hint.get("raw_bytes_base64")
        download_path = hint.get("api_path") or hint.get("download_path")
        download_url = hint.get("download_url")
        filename = hint.get("filename") or f"{item.input_number}.xml"

        result: dict

        if local_path:
            result = ingest_single_file(
                Path(local_path),
                source="local",
                storage=storage,
                bucket=bucket,
            )
        elif bulk_rel_path:
            bulk_path = settings.bulk_root_path / Path(bulk_rel_path)
            result = ingest_single_file(
                bulk_path,
                source="bulk",
                storage=storage,
                bucket=bucket,
            )
        elif raw_base64:
            try:
                data = base64.b64decode(raw_base64)
            except Exception:
                return {
                    "status": "failed",
                    "error_code": "INVALID_INPUT",
                    "error_detail": "raw_base64 is invalid",
                }
            result = ingest_bytes(
                data,
                filename,
                source="api",
                storage=storage,
                bucket=bucket,
                metadata={"input_number": item.input_number},
            )
        elif download_path or download_url:
            try:
                client = JpoApiClient()
                data = client.fetch_bytes(download_url or download_path)
            except ValueError as exc:
                return {
                    "status": "failed",
                    "error_code": "SOURCE_UNAVAILABLE",
                    "error_detail": str(exc),
                }
            result = ingest_bytes(
                data,
                filename,
                source="api",
                storage=storage,
                bucket=bucket,
                metadata={"input_number": item.input_number},
            )
        else:
            return {
                "status": "failed",
                "error_code": "SOURCE_UNAVAILABLE",
                "error_detail": "local_path, bulk_rel_path, raw_base64, or download_url is required",
            }

        if result["status"] == "failed":
            return {
                "status": "failed",
                "error_code": "STORAGE_ERROR",
                "error_detail": result.get("message", "storage failed"),
            }

        raw_file_id = result.get("raw_file_id")
        if raw_file_id:
            hint["raw_file_id"] = raw_file_id
            item.target_version_hint = hint

        return result
