"""Product discovery and ingestion from web/PDF sources."""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse
import uuid

from lxml import html as lxml_html
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core import get_logger
from app.core.config import settings
from app.db.models import (
    Company,
    CompanyProductLink,
    Evidence,
    Product,
    ProductEvidenceLink,
    ProductFieldValue,
    ProductIdentifier,
)
from app.services.normalization import normalize_product_name
from app.services.supabase_storage import SupabaseStorageClient
from app.services.web_crawler import WebCrawler, FetchResult

logger = get_logger(__name__)


MODEL_PATTERN = re.compile(r"\b[A-Z0-9]{1,6}[-_/]?[0-9]{2,6}[A-Z0-9\-_/.]*\b")


@dataclass
class ProductIngestStats:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _store_snapshot(path_hint: str, content: bytes, content_type: str) -> str | None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    sha256 = _hash_bytes(content)
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", path_hint)[:100]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    object_path = f"source=web/acquired_date={date_str}/{sha256[:2]}/{sha256}_{safe_name}"

    client = SupabaseStorageClient(
        bucket=settings.supabase_storage_bucket,
        url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )
    result = client.upload_bytes(object_path, content, content_type or "text/html")
    return f"supabase://{settings.supabase_storage_bucket}/{result.path}"


def _build_evidence(
    db: Session,
    url: str,
    source_type: str,
    content: bytes,
    content_type: str,
    title: str | None,
    raw_meta: dict | None = None,
) -> Evidence:
    content_hash = _hash_bytes(content)
    storage_path = _store_snapshot(url, content, content_type)

    evidence = Evidence(
        url=url,
        source_type=source_type,
        title=title,
        retrieved_at=datetime.now(timezone.utc),
        captured_at=datetime.now(timezone.utc),
        content_hash=content_hash,
        content_type=content_type,
        storage_path=storage_path,
        raw=raw_meta,
    )
    db.add(evidence)
    db.flush()
    return evidence


def _record_product_field(
    db: Session,
    product_id,
    field_name: str,
    value: str | dict | None,
    evidence_id,
    source_type: str,
    source_ref: str | None,
    confidence: float | None,
    captured_at: datetime | None,
) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return

    if isinstance(value, dict):
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    else:
        payload = str(value).encode("utf-8")
    value_hash = hashlib.sha256(payload).hexdigest()

    existing = (
        db.query(ProductFieldValue)
        .filter(
            ProductFieldValue.product_id == product_id,
            ProductFieldValue.field_name == field_name,
            ProductFieldValue.value_hash == value_hash,
        )
        .first()
    )
    if existing:
        if not existing.is_current:
            existing.is_current = True
        return

    db.execute(
        update(ProductFieldValue)
        .where(
            ProductFieldValue.product_id == product_id,
            ProductFieldValue.field_name == field_name,
            ProductFieldValue.is_current.is_(True),
        )
        .values(is_current=False)
    )

    db.add(
        ProductFieldValue(
            product_id=product_id,
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


def _extract_text(doc) -> str:
    return " ".join(doc.xpath("//body//text()")).strip()


def _extract_meta(doc, key: str, attr: str = "name") -> str | None:
    nodes = doc.xpath(f"//meta[@{attr}='{key}']/@content")
    if nodes:
        return nodes[0].strip()
    return None


def _extract_json_ld_products(doc) -> list[dict]:
    nodes = doc.xpath("//script[@type='application/ld+json']/text()")
    products: list[dict] = []

    def collect(obj: object) -> None:
        if isinstance(obj, dict):
            if obj.get("@type") in {"Product", "ProductModel"}:
                products.append(obj)
            for value in obj.values():
                collect(value)
        elif isinstance(obj, list):
            for item in obj:
                collect(item)

    for node in nodes:
        try:
            data = json.loads(node)
        except json.JSONDecodeError:
            continue
        collect(data)

    return products


def _extract_product_from_json_ld(products: list[dict]) -> dict[str, str | None]:
    if not products:
        return {}
    item = products[0]
    brand = item.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")
    model = item.get("model") or item.get("mpn") or item.get("sku")
    category = item.get("category")
    return {
        "name": item.get("name"),
        "description": item.get("description"),
        "brand_name": brand if isinstance(brand, str) else None,
        "model_number": model if isinstance(model, str) else None,
        "category_path": category if isinstance(category, str) else None,
    }


def _extract_breadcrumbs(doc) -> str | None:
    crumbs = doc.xpath("//nav[contains(@class,'breadcrumb')]//li")
    if not crumbs:
        crumbs = doc.xpath("//ol[contains(@class,'breadcrumb')]//li")
    if not crumbs:
        return None
    parts = [c.text_content().strip() for c in crumbs if c.text_content().strip()]
    return " > ".join(parts) if parts else None


def _infer_region(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc.endswith(".jp") or ".co.jp" in parsed.netloc:
        return "JP"
    if "/jp/" in parsed.path:
        return "JP"
    return None


def _infer_status(text: str) -> str:
    lowered = text.lower()
    if "販売終了" in text or "生産終了" in text or "discontinued" in lowered:
        return "discontinued"
    return "active"


def extract_product_fields(html: str, url: str) -> dict[str, str | None]:
    doc = lxml_html.fromstring(html)
    doc.make_links_absolute(url)

    json_ld_fields = _extract_product_from_json_ld(_extract_json_ld_products(doc))

    h1_nodes = doc.xpath("//h1")
    h1 = h1_nodes[0].text_content().strip() if h1_nodes else None
    og_title = _extract_meta(doc, "og:title", attr="property")
    title = (doc.findtext(".//title") or "").strip()
    name = json_ld_fields.get("name") or h1 or og_title or title or None

    meta_desc = _extract_meta(doc, "description")
    paragraphs = [p.text_content().strip() for p in doc.xpath("//p") if p.text_content().strip()]
    description = (
        json_ld_fields.get("description")
        or meta_desc
        or (paragraphs[0] if paragraphs else None)
    )

    text_blob = _extract_text(doc)
    model_match = MODEL_PATTERN.search(text_blob)
    model_number = json_ld_fields.get("model_number") or (model_match.group(0) if model_match else None)

    brand = (
        json_ld_fields.get("brand_name")
        or _extract_meta(doc, "og:site_name", attr="property")
        or _extract_meta(doc, "application-name")
    )
    category_path = json_ld_fields.get("category_path") or _extract_breadcrumbs(doc)
    sale_region = _infer_region(url)
    status = _infer_status(text_blob)

    return {
        "name": name,
        "model_number": model_number,
        "brand_name": brand,
        "category_path": category_path,
        "description": description,
        "sale_region": sale_region,
        "status": status,
    }


def extract_product_fields_from_text(text: str, url: str) -> dict[str, str | None]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else None
    model_match = MODEL_PATTERN.search(text)
    model_number = model_match.group(0) if model_match else None
    description = " ".join(lines[1:4]) if len(lines) > 1 else None
    sale_region = _infer_region(url)
    status = _infer_status(text)
    return {
        "name": name,
        "model_number": model_number,
        "brand_name": None,
        "category_path": None,
        "description": description,
        "sale_region": sale_region,
        "status": status,
    }


def discover_product_links(
    html: str,
    base_url: str,
    allow_pattern: str | None = None,
    deny_pattern: str | None = None,
    max_links: int = 200,
) -> list[str]:
    doc = lxml_html.fromstring(html)
    links = [urljoin(base_url, href) for href in doc.xpath("//a/@href")]

    filtered: list[str] = []
    allow_re = re.compile(allow_pattern) if allow_pattern else None
    deny_re = re.compile(deny_pattern) if deny_pattern else None
    base_netloc = urlparse(base_url).netloc

    for link in links:
        if urlparse(link).netloc != base_netloc:
            continue
        if deny_re and deny_re.search(link):
            continue
        if allow_re and not allow_re.search(link):
            continue
        if not allow_re and not deny_re and "/product" not in link and "/products" not in link:
            continue
        if link not in filtered:
            filtered.append(link)
        if len(filtered) >= max_links:
            break

    return filtered


def upsert_product(
    db: Session,
    company: Company,
    fields: dict[str, str | None],
    evidence: Evidence,
    dry_run: bool = False,
) -> tuple[Product, bool]:
    name = fields.get("name")
    if not name:
        raise ValueError("Product name is required")

    product = (
        db.query(Product)
        .filter(Product.company_id == company.id, Product.name == name)
        .first()
    )
    created = False
    if not product:
        product = Product(
            company_id=company.id,
            name=name,
            model_number=fields.get("model_number"),
            brand_name=fields.get("brand_name"),
            category_path=fields.get("category_path"),
            description=fields.get("description"),
            sale_region=fields.get("sale_region"),
            normalized_name=normalize_product_name(name),
            status=fields.get("status"),
        )
        if not dry_run:
            db.add(product)
            db.flush()
        created = True
    else:
        updated = False
        for key in [
            "model_number",
            "brand_name",
            "category_path",
            "description",
            "sale_region",
            "status",
        ]:
            value = fields.get(key)
            if value and getattr(product, key) != value:
                setattr(product, key, value)
                updated = True
        if updated and not dry_run:
            db.add(product)

    if dry_run:
        return product, created

    for key, value in fields.items():
        _record_product_field(
            db,
            product_id=product.id,
            field_name=key,
            value=value,
            evidence_id=evidence.id,
            source_type="web",
            source_ref=evidence.url,
            confidence=80,
            captured_at=datetime.now(timezone.utc),
        )

    if fields.get("model_number"):
        existing_id = (
            db.query(ProductIdentifier)
            .filter(
                ProductIdentifier.product_id == product.id,
                ProductIdentifier.id_type == "model",
                ProductIdentifier.value == fields["model_number"],
            )
            .first()
        )
        if not existing_id:
            db.add(
                ProductIdentifier(
                    product_id=product.id,
                    id_type="model",
                    value=fields["model_number"],
                    source_evidence_id=evidence.id,
                )
            )

    existing_link = (
        db.query(CompanyProductLink)
        .filter(
            CompanyProductLink.company_id == company.id,
            CompanyProductLink.product_id == product.id,
            CompanyProductLink.role == "manufacturer",
        )
        .first()
    )
    if not existing_link:
        db.add(
            CompanyProductLink(
                company_id=company.id,
                product_id=product.id,
                role="manufacturer",
                link_type="probabilistic",
                confidence_score=70,
                review_status="pending",
                evidence_json={"source": "web", "url": evidence.url},
            )
        )

    link = (
        db.query(ProductEvidenceLink)
        .filter(
            ProductEvidenceLink.product_id == product.id,
            ProductEvidenceLink.evidence_id == evidence.id,
        )
        .first()
    )
    if not link:
        db.add(
            ProductEvidenceLink(
                product_id=product.id,
                evidence_id=evidence.id,
                purpose="product_page",
            )
        )

    db.commit()
    return product, created


def ingest_product_from_fetch(
    db: Session,
    company: Company,
    fetch: FetchResult,
    dry_run: bool = False,
) -> tuple[Product | None, bool]:
    if fetch.content_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # noqa: BLE001
            raise RuntimeError("pypdf is required for PDF extraction") from exc

        reader = PdfReader(io.BytesIO(fetch.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        fields = extract_product_fields_from_text(text, fetch.final_url)
    else:
        html_text = fetch.content.decode("utf-8", errors="replace")
        fields = extract_product_fields(html_text, fetch.final_url)

    if not fields.get("name"):
        return None, False

    evidence = _build_evidence(
        db=db,
        url=fetch.final_url,
        source_type="web",
        content=fetch.content,
        content_type=fetch.content_type or "text/html",
        title=fields.get("name"),
        raw_meta={"status_code": fetch.status_code},
    )

    return upsert_product(db, company, fields, evidence, dry_run=dry_run)


def ingest_product_urls(
    db: Session,
    company_id: str,
    urls: Iterable[str],
    discover: bool = False,
    allow_pattern: str | None = None,
    deny_pattern: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> ProductIngestStats:
    stats = ProductIngestStats()
    crawler = WebCrawler(rate_limit_per_minute=30)

    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError as exc:  # noqa: BLE001
        raise ValueError("Invalid company ID") from exc

    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise ValueError("Company not found")

    queue = list(urls)
    seen: set[str] = set()

    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        if limit and stats.processed >= limit:
            break

        try:
            fetch = crawler.fetch(url)
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.warning("Failed to fetch", url=url, error=str(exc))
            continue

        stats.processed += 1

        if discover and fetch.content_type.startswith("text/html"):
            html_text = fetch.content.decode("utf-8", errors="replace")
            discovered = discover_product_links(
                html_text,
                base_url=fetch.final_url,
                allow_pattern=allow_pattern,
                deny_pattern=deny_pattern,
            )
            for link in discovered:
                if link not in seen:
                    queue.append(link)
            continue

        product, created = ingest_product_from_fetch(db, company, fetch, dry_run=dry_run)
        if not product:
            stats.skipped += 1
            continue
        if created:
            stats.created += 1
        else:
            stats.updated += 1

    return stats
