"""CLI commands using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
import uvicorn
import httpx

from app.core import settings, get_logger


def _load_field_map(
    env_value: str | None,
    file_path: Optional[Path],
    label: str,
) -> dict:
    import json

    if file_path:
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"{label} field map file load failed: {exc}")
            raise typer.Exit(1)

    if not env_value:
        typer.echo(f"{label} field map is required (set env or --field-map-file)")
        raise typer.Exit(1)

    env_value = env_value.strip()
    if env_value.startswith("{"):
        try:
            return json.loads(env_value)
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"{label} field map JSON invalid: {exc}")
            raise typer.Exit(1)

    candidate = Path(env_value)
    if candidate.exists():
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"{label} field map file load failed: {exc}")
            raise typer.Exit(1)

    typer.echo(f"{label} field map is required (set env or --field-map-file)")
    raise typer.Exit(1)

app = typer.Typer(help="Phase2 Patent Storage CLI")
logger = get_logger(__name__)


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Host to bind")] = settings.api_host,
    port: Annotated[int, typer.Option(help="Port to bind")] = settings.api_port,
    reload: Annotated[bool, typer.Option(help="Enable auto-reload")] = False,
) -> None:
    """Start the API server."""
    logger.info("Starting API server", host=host, port=port, reload=reload)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def ingest(
    path: Annotated[Path, typer.Option(help="Path to XML/ZIP files")],
    source: Annotated[str, typer.Option(help="Source identifier")] = "local",
    storage: Annotated[
        str,
        typer.Option(help="Storage backend: local | supabase | both"),
    ] = "local",
    bucket: Annotated[
        Optional[str],
        typer.Option(help="Supabase bucket override (optional)"),
    ] = None,
    ) -> None:
        """Ingest raw XML/ZIP files into storage."""
    from app.ingest.raw_storage import ingest_files

    logger.info("Starting ingest", path=str(path), source=source)
    result = ingest_files(path, source, storage, bucket)
    typer.echo(
        f"Ingested {result['ingested']} files, skipped {result['skipped']} duplicates"
    )


@app.command("auth-approve-user")
def auth_approve_user(
    email: Annotated[str, typer.Option(help="Target user email")],
    approved: Annotated[bool, typer.Option(help="Set approval flag")] = True,
    role: Annotated[Optional[str], typer.Option(help="Set role (optional)")] = None,
) -> None:
    """Approve or revoke a Supabase user."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        typer.echo("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
        raise typer.Exit(1)

    base_url = settings.supabase_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json",
    }

    try:
        response = httpx.get(
            f"{base_url}/auth/v1/admin/users",
            headers=headers,
            params={"email": email},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        typer.echo(f"Failed to lookup user: {exc}")
        raise typer.Exit(1) from exc

    payload = response.json()
    users = payload.get("users") or []
    if not users:
        typer.echo("User not found")
        raise typer.Exit(1)

    user = users[0]
    user_id = user.get("id")
    if not user_id:
        typer.echo("User id missing in response")
        raise typer.Exit(1)

    app_metadata = user.get("app_metadata") or {}
    app_metadata["approved"] = approved
    if role is not None:
        app_metadata["role"] = role

    try:
        update = httpx.put(
            f"{base_url}/auth/v1/admin/users/{user_id}",
            headers=headers,
            json={"app_metadata": app_metadata},
            timeout=10.0,
        )
        update.raise_for_status()
    except httpx.HTTPError as exc:
        typer.echo(f"Failed to update user: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(f"Updated user {email}: approved={approved}" + (f", role={role}" if role else ""))


@app.command()
def parse(
    all_files: Annotated[bool, typer.Option("--all", help="Parse all unparsed files")] = False,
    file_id: Annotated[Optional[str], typer.Option(help="Specific file ID to parse")] = None,
) -> None:
    """Parse ingested XML files to extract claims."""
    from app.parse.jp_gazette_parser import parse_pending_files, parse_single_file

    if file_id:
        logger.info("Parsing single file", file_id=file_id)
        result = parse_single_file(file_id)
        typer.echo(f"Parsed file {file_id}: {result['status']}")
    elif all_files:
        logger.info("Parsing all pending files")
        result = parse_pending_files()
        typer.echo(f"Parsed {result['parsed']} files, failed {result['failed']}")
    else:
        typer.echo("Specify --all or --file-id")
        raise typer.Exit(1)


@app.command()
def ingest_job(
    numbers: Annotated[str, typer.Option(help="Comma-separated patent numbers")],
    input_type: Annotated[
        str, typer.Option(help="Number type: application | publication | registration")
    ] = "publication",
    priority: Annotated[int, typer.Option(help="Job priority (0-10)")] = 5,
    force_refresh: Annotated[bool, typer.Option(help="Force re-ingest")] = False,
    source_preference: Annotated[Optional[str], typer.Option(help="Source preference")] = None,
    idempotency_key: Annotated[Optional[str], typer.Option(help="Idempotency key")] = None,
    local_path: Annotated[
        Optional[Path],
        typer.Option(help="Local raw file path (for current local mode)"),
    ] = None,
) -> None:
    """Create an ingestion job (local_path required for current mode)."""
    from app.db.session import get_db
    from app.services.ingestion_service import IngestionService

    parsed_numbers = [n.strip() for n in numbers.split(",") if n.strip()]
    if not parsed_numbers:
        typer.echo("No valid numbers provided")
        raise typer.Exit(1)

    target_hint = {"local_path": str(local_path)} if local_path else None
    items = [
        {
            "input_number": number,
            "input_number_type": input_type,
            "target_version_hint": target_hint,
        }
        for number in parsed_numbers
    ]

    with get_db() as db:
        service = IngestionService(db)
        job = service.create_job(
            items=items,
            priority=priority,
            force_refresh=force_refresh,
            source_preference=source_preference,
            idempotency_key=idempotency_key,
        )
        typer.echo(f"Created job: {job.job_id}")


@app.command()
def ingest_run(
    job_id: Annotated[str, typer.Option(help="Ingestion job ID")],
    storage: Annotated[
        str,
        typer.Option(help="Storage backend: local | supabase | both"),
    ] = "supabase",
    bucket: Annotated[
        Optional[str],
        typer.Option(help="Supabase bucket override (optional)"),
    ] = None,
) -> None:
    """Run an ingestion job."""
    import json

    from app.db.session import get_db
    from app.services.ingestion_service import IngestionService

    with get_db() as db:
        service = IngestionService(db)
        result = service.run_job(job_id, storage=storage, bucket=bucket)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("company-nta-import")
def company_nta_import(
    path: Annotated[Path, typer.Option(help="NTA CSV/ZIP path")],
    run_type: Annotated[str, typer.Option(help="Run type: full|delta")] = "delta",
    source_url: Annotated[Optional[str], typer.Option(help="Source URL (optional)")] = None,
    encoding: Annotated[Optional[str], typer.Option(help="CSV encoding override")] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
    limit: Annotated[Optional[int], typer.Option(help="Row limit for test runs")] = None,
    priority: Annotated[int, typer.Option(help="Job priority (0-10)")] = 5,
) -> None:
    """Import NTA corporate number data into company master."""
    import json

    from app.db.session import get_db
    from app.services.collection_service import CollectionService
    from app.services.company_ingest import ingest_nta_file

    with get_db() as db:
        service = CollectionService(db)
        job = service.create_job(
            job_type=f"nta_{run_type}",
            items=[
                {
                    "entity_type": "company",
                    "source_type": "nta",
                    "source_ref": str(path),
                    "payload_json": {"run_type": run_type, "source_url": source_url},
                }
            ],
            priority=priority,
        )

        def handler(handler_db, _item):
            stats = ingest_nta_file(
                handler_db,
                path=path,
                run_type=run_type,
                source_url=source_url,
                encoding=encoding,
                dry_run=dry_run,
                limit=limit,
            )
            return {"status": "succeeded", **stats.__dict__}

        result = service.run_job(str(job.job_id), handler)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("company-gbizinfo-import")
def company_gbizinfo_import(
    path: Annotated[Path, typer.Option(help="gBizINFO JSON/ZIP path")],
    run_type: Annotated[str, typer.Option(help="Run type: full|delta")] = "full",
    source_url: Annotated[Optional[str], typer.Option(help="Source URL (optional)")] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
    limit: Annotated[Optional[int], typer.Option(help="Record limit for test runs")] = None,
    priority: Annotated[int, typer.Option(help="Job priority (0-10)")] = 5,
    create_missing: Annotated[
        bool, typer.Option(help="Create company if missing")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option(help="Overwrite existing company fields")
    ] = False,
    include_extra_fields: Annotated[
        bool, typer.Option(help="Record extra fields (industry, business_items, etc.)")
    ] = False,
    include_patent: Annotated[
        bool, typer.Option(help="Record patent list (large)")
    ] = False,
    include_subsidy: Annotated[
        bool, typer.Option(help="Record subsidy list (large)")
    ] = False,
    batch_size: Annotated[int, typer.Option(help="DB commit batch size")] = 500,
    hash_content: Annotated[
        bool, typer.Option(help="Compute file hash for evidence (slow on large files)")
    ] = False,
) -> None:
    """Import gBizINFO bulk JSON into company master."""
    import json

    from app.db.session import get_db
    from app.services.collection_service import CollectionService
    from app.services.company_ingest import ingest_gbizinfo_path

    with get_db() as db:
        if dry_run:
            stats = ingest_gbizinfo_path(
                db,
                path=path,
                run_type=run_type,
                source_url=source_url,
                dry_run=True,
                limit=limit,
                batch_size=batch_size,
                create_missing=create_missing,
                overwrite=overwrite,
                include_extra_fields=include_extra_fields,
                include_patent=include_patent,
                include_subsidy=include_subsidy,
                hash_content=hash_content,
            )
            typer.echo(json.dumps({"status": "dry_run", **stats.__dict__}, ensure_ascii=False, indent=2))
            return

        service = CollectionService(db)
        job = service.create_job(
            job_type=f"gbizinfo_{run_type}",
            items=[
                {
                    "entity_type": "company",
                    "source_type": "gbizinfo",
                    "source_ref": str(path),
                    "payload_json": {
                        "run_type": run_type,
                        "source_url": source_url,
                        "create_missing": create_missing,
                        "overwrite": overwrite,
                        "include_extra_fields": include_extra_fields,
                        "include_patent": include_patent,
                        "include_subsidy": include_subsidy,
                        "batch_size": batch_size,
                        "hash_content": hash_content,
                    },
                }
            ],
            priority=priority,
        )

        def handler(handler_db, _item):
            stats = ingest_gbizinfo_path(
                handler_db,
                path=path,
                run_type=run_type,
                source_url=source_url,
                dry_run=False,
                limit=limit,
                batch_size=batch_size,
                create_missing=create_missing,
                overwrite=overwrite,
                include_extra_fields=include_extra_fields,
                include_patent=include_patent,
                include_subsidy=include_subsidy,
                hash_content=hash_content,
            )
            return {"status": "succeeded", **stats.__dict__}

        result = service.run_job(str(job.job_id), handler)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("company-seed-patents")
def company_seed_patents(
    limit: Annotated[int, typer.Option(help="Max applicants to process")] = 500,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
) -> None:
    """Seed companies from JP applicant names and create probabilistic links."""
    import json

    from app.db.session import get_db
    from app.services.company_ingest import seed_companies_from_patents

    with get_db() as db:
        result = seed_companies_from_patents(db, limit=limit, dry_run=dry_run)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("company-enrich-gbiz")
def company_enrich_gbiz(
    corporate_number: Annotated[str, typer.Option(help="Corporate number (13 digits)")],
    company_id: Annotated[Optional[str], typer.Option(help="Company UUID override")] = None,
    field_map_file: Annotated[
        Optional[Path], typer.Option(help="Field map JSON file path")
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
) -> None:
    """Enrich company using gBizINFO API (field map required)."""
    import json

    from app.db.session import get_db
    from app.db.models import Company
    from app.services.company_ingest import apply_company_enrichment
    from app.services.company_sources import GbizinfoClient, extract_fields
    from app.core.config import settings

    mapping = _load_field_map(settings.gbizinfo_field_map, field_map_file, "GBIZINFO")
    client = GbizinfoClient()
    payload = client.fetch_by_corporate_number(corporate_number)
    fields = extract_fields(payload, mapping)

    with get_db() as db:
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
        else:
            company = db.query(Company).filter(Company.corporate_number == corporate_number).first()
        if not company:
            typer.echo("Company not found")
            raise typer.Exit(1)

        result = apply_company_enrichment(
            db=db,
            company=company,
            fields=fields,
            source_type="gbizinfo",
            source_url=settings.gbizinfo_api_base_url,
            payload=payload,
            confidence=80,
            dry_run=dry_run,
        )
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("company-enrich-edinet")
def company_enrich_edinet(
    edinet_code: Annotated[str, typer.Option(help="EDINET code")],
    company_id: Annotated[Optional[str], typer.Option(help="Company UUID override")] = None,
    field_map_file: Annotated[
        Optional[Path], typer.Option(help="Field map JSON file path")
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
) -> None:
    """Enrich company using EDINET API (field map required)."""
    import json

    from app.db.session import get_db
    from app.db.models import Company, CompanyIdentifier
    from app.services.company_ingest import apply_company_enrichment
    from app.services.company_sources import EdinetClient, extract_fields
    from app.core.config import settings

    mapping = _load_field_map(settings.edinet_field_map, field_map_file, "EDINET")
    client = EdinetClient()
    payload = client.fetch(edinet_code)
    fields = extract_fields(payload, mapping)

    with get_db() as db:
        company = None
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            identifier = (
                db.query(CompanyIdentifier)
                .filter(
                    CompanyIdentifier.id_type == "edinet",
                    CompanyIdentifier.value == edinet_code,
                )
                .first()
            )
            if identifier:
                company = identifier.company
        if not company:
            typer.echo("Company not found")
            raise typer.Exit(1)

        result = apply_company_enrichment(
            db=db,
            company=company,
            fields=fields,
            source_type="edinet",
            source_url=settings.edinet_api_base_url,
            payload=payload,
            confidence=70,
            dry_run=dry_run,
        )
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("product-web-import")
def product_web_import(
    company_id: Annotated[str, typer.Option(help="Company UUID")],
    urls: Annotated[str, typer.Option(help="Comma-separated product or list URLs")],
    discover: Annotated[bool, typer.Option(help="Discover product links from list pages")] = False,
    allow_pattern: Annotated[Optional[str], typer.Option(help="Regex to allow URLs")] = None,
    deny_pattern: Annotated[Optional[str], typer.Option(help="Regex to deny URLs")] = None,
    limit: Annotated[Optional[int], typer.Option(help="Max pages to process")] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
) -> None:
    """Import products from web pages (official site)."""
    import json

    from app.db.session import get_db
    from app.services.product_ingest import ingest_product_urls

    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    if not url_list:
        typer.echo("No valid URLs provided")
        raise typer.Exit(1)

    with get_db() as db:
        stats = ingest_product_urls(
            db=db,
            company_id=company_id,
            urls=url_list,
            discover=discover,
            allow_pattern=allow_pattern,
            deny_pattern=deny_pattern,
            limit=limit,
            dry_run=dry_run,
        )
        typer.echo(json.dumps(stats.__dict__, ensure_ascii=False, indent=2))


@app.command("link-patents-by-name")
def link_patents_by_name(
    limit: Annotated[int, typer.Option(help="Max applicant links to process")] = 1000,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no DB writes)")] = False,
) -> None:
    """Create patent-company links based on name matching."""
    import json

    from app.db.session import get_db
    from app.services.linking_service import link_patents_by_name as link_service

    with get_db() as db:
        result = link_service(db, limit=limit, dry_run=dry_run)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("collection-metrics")
def collection_metrics() -> None:
    """Print collection job/item metrics."""
    import json

    from sqlalchemy import func

    from app.db.session import get_db
    from app.db.models import CollectionJob, CollectionItem

    with get_db() as db:
        job_counts = (
            db.query(CollectionJob.status, func.count(CollectionJob.job_id))
            .group_by(CollectionJob.status)
            .all()
        )
        item_counts = (
            db.query(CollectionItem.status, func.count(CollectionItem.item_id))
            .group_by(CollectionItem.status)
            .all()
        )

    typer.echo(
        json.dumps(
            {
                "jobs": {status: count for status, count in job_counts},
                "items": {status: count for status, count in item_counts},
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command()
def fetch(
    patent_number: Annotated[str, typer.Argument(help="Patent number (e.g., JP7410975B2, 特許第1234567号)")],
    provider: Annotated[str, typer.Option(help="Provider: gemini, codex, claude, all")] = "gemini",
    save: Annotated[bool, typer.Option(help="Save to database")] = True,
    compare: Annotated[bool, typer.Option(help="Compare results from multiple providers")] = False,
    output: Annotated[Optional[Path], typer.Option(help="Output JSON file path")] = None,
) -> None:
    """Fetch patent data from JPO via CLI tools (gemini/codex/claude)."""
    import json
    import subprocess
    import concurrent.futures

    if compare or provider == "all":
        typer.echo(f"Fetching {patent_number} from multiple LLMs...")
        _fetch_and_compare(patent_number, save)
        return

    logger.info("Fetching patent data", patent_number=patent_number, provider=provider)
    typer.echo(f"Fetching {patent_number} via {provider}...")

    prompt = f"""J-PlatPatで{patent_number}を検索し、JSON形式で出力: title, abstract, assignee, filing_date, claims(1:全文, 2:全文), ipc_codes。説明不要JSONのみ"""

    try:
        if provider == "gemini":
            result = _fetch_with_gemini(prompt)
        elif provider == "codex":
            result = _fetch_with_codex(prompt)
        else:
            # Fallback to OpenAI API
            import asyncio
            from app.llm.deep_research import DeepResearchProvider
            result = asyncio.run(DeepResearchProvider().search_patent(patent_number))

        typer.echo("\n" + "=" * 60)
        typer.echo("Result:")
        typer.echo("=" * 60)

        if isinstance(result, dict):
            output_json = json.dumps(result, ensure_ascii=False, indent=2)

            # Save to file if specified
            if output:
                output.write_text(output_json, encoding='utf-8')
                typer.echo(f"Saved to: {output}")
            else:
                # Print with ASCII escaping on Windows
                import sys
                if sys.platform == "win32":
                    typer.echo(json.dumps(result, ensure_ascii=True, indent=2))
                else:
                    typer.echo(output_json)

            if save:
                _save_patent_to_db(patent_number, result)
                typer.echo("\n[OK] Saved to database")
        else:
            typer.echo(str(result))

    except Exception as e:
        typer.echo(f"\n✗ エラー: {e}", err=True)
        raise typer.Exit(1)


@app.command("jp-index-import")
def jp_index_import(
    path: Annotated[Path, typer.Option(help="Path to normalized JSONL file")],
    source: Annotated[str, typer.Option(help="Source identifier")] = "bulk",
    run_type: Annotated[str, typer.Option(help="Run type: full/delta/weekly/authority")] = "delta",
    update_date: Annotated[Optional[str], typer.Option(help="Update date (YYYY-MM-DD)")] = None,
    batch_key: Annotated[Optional[str], typer.Option(help="Batch key override")] = None,
    dry_run: Annotated[bool, typer.Option(help="Dry run (no commit)")] = False,
) -> None:
    """Import normalized JSONL data into JP Patent Index."""
    from app.db.session import get_db
    from app.jp_index.ingest import create_ingest_batch, ingest_normalized_jsonl, parse_date

    parsed_date = parse_date(update_date) if update_date else None
    key = batch_key or f"{source}:{run_type}:{parsed_date or 'unknown'}:{path.name}"

    with get_db() as db:
        batch = create_ingest_batch(
            db=db,
            source=source,
            run_type=run_type,
            update_date=parsed_date,
            batch_key=key,
            metadata={"file": str(path)},
        )
        result = ingest_normalized_jsonl(db, path, batch, source, dry_run=dry_run)

    typer.echo(f"Imported {result['records']} records (errors={result['errors']})")


def _fetch_with_gemini(prompt: str) -> dict:
    """Fetch patent data using Gemini CLI."""
    logger.info("Running Gemini CLI")
    return _run_cli("gemini", prompt)


def _fetch_with_codex(prompt: str) -> dict:
    """Fetch patent data using Codex CLI."""
    logger.info("Running Codex CLI")
    return _run_cli("codex", prompt)


def _extract_json(text: str) -> dict:
    """Extract JSON from text output."""
    import json
    import re

    # Try to find JSON block
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try parsing entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


def _fetch_and_compare(patent_number: str, save: bool) -> None:
    """Fetch patent data from multiple providers and compare."""
    import json
    import subprocess
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed

    prompt = f"""J-PlatPatで{patent_number}を検索し、JSON形式で出力: title, abstract, assignee, filing_date, claims(1:全文, 2:全文), ipc_codes。説明不要JSONのみ"""

    providers = {
        "gemini": lambda: _run_cli("gemini", prompt),
        "codex": lambda: _run_cli("codex", prompt),
        "claude": lambda: _run_cli("claude", prompt),
    }

    results = {}

    typer.echo("\n並列取得開始...")
    typer.echo("-" * 60)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn): name for name, fn in providers.items()}

        for future in as_completed(futures, timeout=180):
            name = futures[future]
            try:
                result = future.result()
                results[name] = result
                typer.echo(f"✓ {name}: 取得完了")
            except Exception as e:
                results[name] = {"error": str(e)}
                typer.echo(f"✗ {name}: エラー - {e}")

    # Display comparison
    typer.echo("\n" + "=" * 60)
    typer.echo("比較結果")
    typer.echo("=" * 60)

    for provider_name, data in results.items():
        typer.echo(f"\n【{provider_name.upper()}】")
        typer.echo("-" * 40)
        if "error" in data:
            typer.echo(f"エラー: {data['error']}")
        else:
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
            if len(json.dumps(data)) > 2000:
                typer.echo("... (truncated)")

    # Save best result
    if save:
        for provider_name in ["claude", "gemini", "codex"]:
            if provider_name in results and "error" not in results[provider_name]:
                _save_patent_to_db(patent_number, results[provider_name])
                typer.echo(f"\n✓ {provider_name}の結果をデータベースに保存しました")
                break


def _run_cli(cli_name: str, prompt: str) -> dict:
    """Run a CLI tool and return the result."""
    import subprocess
    import sys
    import tempfile
    import os

    # Write prompt to temp file to avoid shell escaping issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        if cli_name == "claude":
            # claude --print "prompt" --output-format json
            cmd = ["claude", "--print", "--output-format", "json"]
        elif cli_name == "codex":
            # codex exec "prompt"
            cmd = ["codex", "exec"]
        elif cli_name == "gemini":
            # gemini -p "prompt" -o json
            cmd = ["gemini", "-o", "json"]
        else:
            raise ValueError(f"Unknown CLI: {cli_name}")

        # Read prompt from file via stdin
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_text = f.read()

        if sys.platform == "win32":
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            if cli_name == "claude":
                cmd_str = f'claude --print --output-format json "{prompt_text[:500]}"'
            elif cli_name == "codex":
                cmd_str = f'codex exec "{prompt_text[:500]}"'
            elif cli_name == "gemini":
                cmd_str = f'gemini -p "{prompt_text[:500]}" -o json'

            # Use Popen for better control over encoding
            process = subprocess.Popen(
                cmd_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                env=env,
            )
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=180)
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                raise Exception(f"{cli_name} timed out")

            class Result:
                pass
            result = Result()
            result.returncode = returncode
            result.stdout = stdout
            result.stderr = stderr
        else:
            cmd.append(prompt_text)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

        if result.returncode != 0:
            raise Exception(f"{cli_name} failed: {result.stderr[:200]}")

        return _extract_json(result.stdout.strip())

    finally:
        os.unlink(prompt_file)


def _save_patent_to_db(patent_number: str, data: dict) -> None:
    """Save fetched patent data to database."""
    from app.db.session import get_db
    from app.db.models import Document, Claim, DocumentText
    import re

    # Normalize patent number
    doc_number = re.sub(r'[^0-9]', '', patent_number)[-7:]
    country = "JP"
    kind = "B2"

    if "B2" in patent_number.upper():
        kind = "B2"
    elif "A" in patent_number.upper():
        kind = "A"

    with get_db() as db:
        # Check if document exists
        existing = db.query(Document).filter(
            Document.doc_number == doc_number,
            Document.country == country,
        ).first()

        if existing:
            logger.info("Document already exists, updating", doc_id=existing.id)
            doc = existing
        else:
            doc = Document(
                country=country,
                doc_number=doc_number,
                kind=kind,
                title=data.get("title") or data.get("発明の名称"),
                abstract=data.get("abstract") or data.get("要約"),
                assignee=data.get("assignee") or data.get("出願人"),
                filing_date=data.get("filing_date") or data.get("出願日"),
            )
            db.add(doc)
            db.flush()

        # Add claims
        claims = data.get("claims") or data.get("請求項") or []
        if isinstance(claims, dict):
            claims = [{"claim_no": k, "claim_text": v} for k, v in claims.items()]
        elif isinstance(claims, str):
            claims = [{"claim_no": 1, "claim_text": claims}]

        # Also check for claim_1, claim1, 請求項1 etc.
        if not claims:
            for key in ["claim_1", "claim1", "請求項1", "請求項１"]:
                if key in data:
                    claims.append({"claim_no": 1, "claim_text": data[key]})
                    break

        for claim_data in claims:
            claim_no = claim_data.get("claim_no") or claim_data.get("番号") or 1
            claim_text = claim_data.get("claim_text") or claim_data.get("テキスト") or claim_data.get("text")
            if claim_text:
                existing_claim = db.query(Claim).filter(
                    Claim.document_id == doc.id,
                    Claim.claim_no == int(claim_no),
                ).first()
                if not existing_claim:
                    db.add(Claim(
                        document_id=doc.id,
                        claim_no=int(claim_no),
                        claim_text=str(claim_text),
                        source="jplatpat",
                        is_current=True,
                    ))

        # Add specification/description if available
        spec_text = (
            data.get("specification")
            or data.get("detailed_description")
            or data.get("description")
            or data.get("発明の詳細な説明")
            or data.get("明細書")
        )
        if spec_text:
            existing_text = (
                db.query(DocumentText)
                .filter(
                    DocumentText.document_id == doc.id,
                    DocumentText.text_type == "specification",
                    DocumentText.is_current.is_(True),
                )
                .first()
            )
            if existing_text:
                existing_text.text = str(spec_text)
                existing_text.source = existing_text.source or "jplatpat"
            else:
                db.add(
                    DocumentText(
                        document_id=doc.id,
                        text_type="specification",
                        language="ja",
                        source="jplatpat",
                        is_current=True,
                        text=str(spec_text),
                    )
                )

        db.commit()
        logger.info("Patent saved to database", doc_id=doc.id, claims_count=len(claims))


runs_app = typer.Typer(help="Manage ingest runs")
app.add_typer(runs_app, name="runs")


@runs_app.command("list")
def list_runs(
    limit: Annotated[int, typer.Option(help="Number of runs to show")] = 10,
) -> None:
    """List recent ingest runs."""
    from app.db.session import get_db
    from app.db.models import IngestRun

    with get_db() as db:
        runs = db.query(IngestRun).order_by(IngestRun.started_at.desc()).limit(limit).all()

    if not runs:
        typer.echo("No runs found")
        return

    for run in runs:
        status_icon = "✓" if run.status == "completed" else "✗" if run.status == "failed" else "…"
        typer.echo(f"{status_icon} {run.id} | {run.run_type} | {run.started_at} | {run.status}")


if __name__ == "__main__":
    app()
