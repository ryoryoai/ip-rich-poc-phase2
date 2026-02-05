"""Raw file storage with SHA-256 deduplication."""

import hashlib
import mimetypes
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from app.core import settings, get_logger
from app.db.session import get_db
from app.db.models import RawFile, IngestRun
from app.services.supabase_storage import SupabaseStorageClient

logger = get_logger(__name__)


class IngestResult(TypedDict):
    """Result of an ingest operation."""

    ingested: int
    skipped: int
    failed: int
    errors: list[str]


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hash of bytes."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()


def _sanitize_filename(name: str) -> str:
    return name.replace("\\", "_").replace("/", "_")


def build_object_path(source: str, sha256: str, original_name: str, acquired_date: str) -> str:
    """
    Build object path using content-addressable structure.

    Format: source=local/acquired_date=YYYY-MM-DD/ab/abcd1234.../filename.xml
    """
    prefix = sha256[:2]
    safe_name = _sanitize_filename(original_name)
    return f"source={source}/acquired_date={acquired_date}/{prefix}/{sha256}_{safe_name}"


def get_storage_paths(
    source: str,
    sha256: str,
    original_name: str,
    acquired_date: str,
) -> tuple[Path, str]:
    """Return local storage path and object path."""
    object_path = build_object_path(source, sha256, original_name, acquired_date)
    storage_path = settings.raw_storage_path / Path(object_path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    return storage_path, object_path


def _merge_storage_provider(current: str | None, incoming: str) -> str:
    if not current:
        return incoming
    if current == incoming:
        return current
    return "both"


def ingest_single_file(
    file_path: Path,
    source: str = "local",
    storage: str = "local",
    bucket: str | None = None,
) -> dict[str, str]:
    """
    Ingest a single file into storage.

    Returns:
        dict with 'status' ('ingested', 'skipped', 'failed') and 'message'
    """
    if not file_path.exists():
        return {"status": "failed", "message": f"File not found: {file_path}"}

    storage_mode = storage.lower()
    if storage_mode not in {"local", "supabase", "both"}:
        return {"status": "failed", "message": f"Invalid storage mode: {storage}"}

    use_local = storage_mode in {"local", "both"}
    use_supabase = storage_mode in {"supabase", "both"}

    sha256 = calculate_sha256(file_path)
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    size_bytes = file_path.stat().st_size

    with get_db() as db:
        # Check for duplicate
        existing = db.query(RawFile).filter(RawFile.sha256 == sha256).first()
        if existing:
            if use_supabase and not existing.object_path:
                acquired_at = existing.acquired_at or datetime.now(timezone.utc)
                acquired_date = acquired_at.strftime("%Y-%m-%d")
                object_path = build_object_path(source, sha256, file_path.name, acquired_date)
                try:
                    storage_client = SupabaseStorageClient(
                        bucket=bucket or settings.supabase_patent_raw_bucket
                    )
                    upload_result = storage_client.upload_bytes(
                        object_path, file_path.read_bytes(), content_type
                    )
                except ValueError as exc:
                    return {"status": "failed", "message": str(exc)}

                existing.storage_provider = _merge_storage_provider(
                    existing.storage_provider, "supabase"
                )
                existing.bucket = bucket or settings.supabase_patent_raw_bucket
                existing.object_path = object_path
                existing.mime_type = existing.mime_type or content_type
                existing.size_bytes = existing.size_bytes or size_bytes
                existing.etag = upload_result.etag or existing.etag
                db.commit()
                logger.info(
                    "Uploaded existing raw file to Supabase",
                    sha256=sha256,
                    object_path=object_path,
                )
                return {
                    "status": "ingested",
                    "message": f"Uploaded to Supabase: {object_path}",
                    "raw_file_id": str(existing.id),
                }

            logger.info("Skipping duplicate file", sha256=sha256, original=file_path.name)
            return {"status": "skipped", "message": f"Duplicate: {sha256}"}

        acquired_at = datetime.now(timezone.utc)
        acquired_date = acquired_at.strftime("%Y-%m-%d")
        storage_path = None
        object_path = build_object_path(source, sha256, file_path.name, acquired_date)
        upload_result = None

        if use_local:
            storage_path, object_path = get_storage_paths(
                source, sha256, file_path.name, acquired_date
            )
            shutil.copy2(file_path, storage_path)

        if use_supabase:
            try:
                storage_client = SupabaseStorageClient(
                    bucket=bucket or settings.supabase_patent_raw_bucket
                )
                upload_result = storage_client.upload_bytes(
                    object_path, file_path.read_bytes(), content_type
                )
            except ValueError as exc:
                return {"status": "failed", "message": str(exc)}

        # Create database record
        stored_path = (
            str(storage_path)
            if storage_path is not None
            else f"supabase://{bucket or settings.supabase_patent_raw_bucket}/{object_path}"
        )
        storage_provider = (
            "both" if (use_local and use_supabase) else "supabase" if use_supabase else "local"
        )
        raw_file = RawFile(
            source=source,
            original_name=file_path.name,
            sha256=sha256,
            stored_path=stored_path,
            storage_provider=storage_provider,
            bucket=bucket or settings.supabase_patent_raw_bucket if use_supabase else None,
            object_path=object_path if use_supabase else None,
            mime_type=content_type,
            size_bytes=size_bytes,
            etag=upload_result.etag if upload_result else None,
            acquired_at=acquired_at,
            metadata_json={"original_path": str(file_path), "storage": storage_provider},
        )
        db.add(raw_file)
        db.flush()

        logger.info(
            "Ingested file",
            sha256=sha256,
            original=file_path.name,
            stored_path=stored_path,
        )
        return {
            "status": "ingested",
            "message": f"Stored at {stored_path}",
            "raw_file_id": str(raw_file.id),
        }


def ingest_files(
    path: Path,
    source: str = "local",
    storage: str = "local",
    bucket: str | None = None,
) -> IngestResult:
    """
    Ingest multiple files from a directory.

    Supports:
    - Individual XML files
    - ZIP archives (extracted and processed)
    """
    result: IngestResult = {"ingested": 0, "skipped": 0, "failed": 0, "errors": []}

    with get_db() as db:
        # Create ingest run record
        run = IngestRun(
            run_type="ingest",
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(run)
        db.flush()
        run_id = run.id

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.glob("**/*.xml")) + list(path.glob("**/*.zip"))
    else:
        result["failed"] = 1
        result["errors"].append(f"Invalid path: {path}")
        return result

    for file_path in files:
        try:
            if file_path.suffix.lower() == ".zip":
                # Extract ZIP and process contents
                zip_result = _process_zip(file_path, source, storage, bucket)
                result["ingested"] += zip_result["ingested"]
                result["skipped"] += zip_result["skipped"]
                result["failed"] += zip_result["failed"]
                result["errors"].extend(zip_result["errors"])
            else:
                # Process single file
                single_result = ingest_single_file(file_path, source, storage, bucket)
                if single_result["status"] == "ingested":
                    result["ingested"] += 1
                elif single_result["status"] == "skipped":
                    result["skipped"] += 1
                else:
                    result["failed"] += 1
                    result["errors"].append(single_result["message"])
        except Exception as e:
            logger.exception("Failed to process file", file=str(file_path))
            result["failed"] += 1
            result["errors"].append(f"{file_path}: {e}")

    # Update ingest run
    with get_db() as db:
        run = db.query(IngestRun).filter(IngestRun.id == run_id).first()
        if run:
            run.finished_at = datetime.now(timezone.utc)
            run.status = "completed" if result["failed"] == 0 else "partial"
            run.detail_json = {
                "ingested": result["ingested"],
                "skipped": result["skipped"],
                "failed": result["failed"],
            }

    return result


def ingest_bytes(
    data: bytes,
    original_name: str,
    source: str = "api",
    storage: str = "supabase",
    bucket: str | None = None,
    metadata: dict | None = None,
) -> dict[str, str]:
    """Ingest raw bytes into storage."""
    storage_mode = storage.lower()
    if storage_mode not in {"local", "supabase", "both"}:
        return {"status": "failed", "message": f"Invalid storage mode: {storage}"}

    use_local = storage_mode in {"local", "both"}
    use_supabase = storage_mode in {"supabase", "both"}

    sha256 = calculate_sha256_bytes(data)
    content_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
    size_bytes = len(data)

    with get_db() as db:
        existing = db.query(RawFile).filter(RawFile.sha256 == sha256).first()
        if existing:
            if use_supabase and not existing.object_path:
                acquired_at = existing.acquired_at or datetime.now(timezone.utc)
                acquired_date = acquired_at.strftime("%Y-%m-%d")
                object_path = build_object_path(source, sha256, original_name, acquired_date)
                try:
                    storage_client = SupabaseStorageClient(
                        bucket=bucket or settings.supabase_patent_raw_bucket
                    )
                    upload_result = storage_client.upload_bytes(
                        object_path, data, content_type
                    )
                except ValueError as exc:
                    return {"status": "failed", "message": str(exc)}

                existing.storage_provider = _merge_storage_provider(
                    existing.storage_provider, "supabase"
                )
                existing.bucket = bucket or settings.supabase_patent_raw_bucket
                existing.object_path = object_path
                existing.mime_type = existing.mime_type or content_type
                existing.size_bytes = existing.size_bytes or size_bytes
                existing.etag = upload_result.etag or existing.etag
                db.commit()
                return {
                    "status": "ingested",
                    "message": f"Uploaded to Supabase: {object_path}",
                    "raw_file_id": str(existing.id),
                }

            return {"status": "skipped", "message": f"Duplicate: {sha256}"}

        acquired_at = datetime.now(timezone.utc)
        acquired_date = acquired_at.strftime("%Y-%m-%d")
        storage_path = None
        object_path = build_object_path(source, sha256, original_name, acquired_date)
        upload_result = None

        if use_local:
            storage_path, object_path = get_storage_paths(
                source, sha256, original_name, acquired_date
            )
            storage_path.write_bytes(data)

        if use_supabase:
            try:
                storage_client = SupabaseStorageClient(
                    bucket=bucket or settings.supabase_patent_raw_bucket
                )
                upload_result = storage_client.upload_bytes(
                    object_path, data, content_type
                )
            except ValueError as exc:
                return {"status": "failed", "message": str(exc)}

        stored_path = (
            str(storage_path)
            if storage_path is not None
            else f"supabase://{bucket or settings.supabase_patent_raw_bucket}/{object_path}"
        )
        storage_provider = (
            "both" if (use_local and use_supabase) else "supabase" if use_supabase else "local"
        )

        raw_file = RawFile(
            source=source,
            original_name=original_name,
            sha256=sha256,
            stored_path=stored_path,
            storage_provider=storage_provider,
            bucket=bucket or settings.supabase_patent_raw_bucket if use_supabase else None,
            object_path=object_path if use_supabase else None,
            mime_type=content_type,
            size_bytes=size_bytes,
            etag=upload_result.etag if upload_result else None,
            acquired_at=acquired_at,
            metadata_json=metadata or {"storage": storage_provider},
        )
        db.add(raw_file)
        db.flush()

        return {
            "status": "ingested",
            "message": f"Stored at {stored_path}",
            "raw_file_id": str(raw_file.id),
        }


def _process_zip(
    zip_path: Path,
    source: str,
    storage: str,
    bucket: str | None,
) -> IngestResult:
    """Extract and process files from a ZIP archive."""
    result: IngestResult = {"ingested": 0, "skipped": 0, "failed": 0, "errors": []}

    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_path)
        except zipfile.BadZipFile as e:
            result["failed"] = 1
            result["errors"].append(f"Bad ZIP file {zip_path}: {e}")
            return result

        # Process extracted XML files
        for xml_file in temp_path.glob("**/*.xml"):
            single_result = ingest_single_file(xml_file, source, storage, bucket)
            if single_result["status"] == "ingested":
                result["ingested"] += 1
            elif single_result["status"] == "skipped":
                result["skipped"] += 1
            else:
                result["failed"] += 1
                result["errors"].append(single_result["message"])

    return result
