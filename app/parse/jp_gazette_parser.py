"""Japanese patent gazette XML parser."""

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone, date
from pathlib import Path
from typing import TypedDict

from lxml import etree

from app.core import get_logger, settings
from app.db.session import get_db
from app.db.models import (
    RawFile,
    Document,
    Claim,
    DocumentText,
    IngestRun,
    Patent,
    PatentNumberSource,
    PatentVersion,
    PatentClaim,
    PatentSpecSection,
)
from app.services.supabase_storage import SupabaseStorageClient

logger = get_logger(__name__)


class ParsedDocument(TypedDict):
    """Parsed document data."""

    country: str
    doc_number: str
    kind: str | None
    publication_date: str | None
    claims: list[dict[str, str | int]]
    specification_text: str | None
    spec_sections: list[dict[str, str]]
    abstract_text: str | None
    drawing_description_text: str | None


class ParseResult(TypedDict):
    """Result of parse operation."""

    parsed: int
    failed: int
    errors: list[str]


NORM_VERSION = "v1"


def normalize_claim_text(text: str) -> str:
    """
    Normalize claim text.

    - Strip leading/trailing whitespace from lines
    - Collapse multiple blank lines into one
    - Remove excessive whitespace
    """
    if not text:
        return ""

    lines = text.split("\n")
    normalized_lines = [line.strip() for line in lines]

    # Collapse multiple blank lines
    result_lines = []
    prev_blank = False
    for line in normalized_lines:
        is_blank = len(line) == 0
        if is_blank and prev_blank:
            continue
        result_lines.append(line)
        prev_blank = is_blank

    return "\n".join(result_lines).strip()


def normalize_long_text(text: str) -> str:
    """Normalize long-form text (specification, description, etc.)."""
    if not text:
        return ""

    lines = text.splitlines()
    normalized_lines = [line.strip() for line in lines]

    result_lines = []
    prev_blank = False
    for line in normalized_lines:
        is_blank = len(line) == 0
        if is_blank and prev_blank:
            continue
        result_lines.append(line)
        prev_blank = is_blank

    return "\n".join(result_lines).strip()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_jp_gazette_xml(xml_path: Path) -> ParsedDocument | None:
    """Parse a Japanese patent gazette XML file from a path."""
    try:
        xml_bytes = xml_path.read_bytes()
    except Exception as exc:
        logger.exception("Failed to read XML", file=str(xml_path), error=str(exc))
        return None
    return parse_jp_gazette_xml_bytes(xml_bytes, origin=str(xml_path))


def parse_jp_gazette_xml_bytes(xml_bytes: bytes, origin: str | None = None) -> ParsedDocument | None:
    """
    Parse a Japanese patent gazette XML file from bytes.

    Supports multiple XML formats:
    - JP-B2 (granted patents)
    - JP-A (applications)
    """
    try:
        root = _parse_xml_bytes(xml_bytes)
        if root is None:
            return None

        # Extract document identification
        doc_info = _extract_doc_info(root)
        if not doc_info:
            logger.warning("Could not extract document info", file=origin or "bytes")
            return None

        # Extract claims and spec sections
        claims = _extract_claims(root)
        specification_text = _extract_specification(root)
        spec_sections = _extract_spec_sections(root, specification_text)
        abstract_text = _extract_abstract(root)
        drawing_description_text = _extract_drawing_description(root)

        return ParsedDocument(
            country=doc_info.get("country", "JP"),
            doc_number=doc_info.get("doc_number", ""),
            kind=doc_info.get("kind"),
            publication_date=doc_info.get("publication_date"),
            claims=claims,
            specification_text=specification_text,
            spec_sections=spec_sections,
            abstract_text=abstract_text,
            drawing_description_text=drawing_description_text,
        )

    except Exception as e:
        logger.exception("Failed to parse XML", file=origin or "bytes", error=str(e))
        return None


def _parse_xml_bytes(xml_bytes: bytes) -> etree._Element | None:
    """Parse XML bytes with encoding fallbacks."""
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    try:
        return etree.fromstring(xml_bytes, parser)
    except Exception:
        if b"encoding=" in xml_bytes[:200]:
            try:
                return etree.fromstring(xml_bytes)
            except Exception:
                return None
        parser = etree.XMLParser(recover=True, encoding="shift_jis")
        try:
            return etree.fromstring(xml_bytes, parser)
        except Exception:
            return None


def _extract_doc_info(root: etree._Element) -> dict[str, str] | None:
    """Extract document identification from XML."""
    info: dict[str, str] = {}

    # Try different XML structures
    # Format 1: publication-reference/document-id
    pub_ref = root.find(".//publication-reference/document-id")
    if pub_ref is not None:
        country = pub_ref.findtext("country")
        doc_number = pub_ref.findtext("doc-number")
        kind = pub_ref.findtext("kind")
        date = pub_ref.findtext("date")

        if doc_number:
            info["country"] = country or "JP"
            info["doc_number"] = doc_number
            if kind:
                info["kind"] = kind
            if date:
                info["publication_date"] = date
            return info

    # Format 2: bibliographic-data
    bib = root.find(".//bibliographic-data")
    if bib is not None:
        pub = bib.find(".//publication-reference/document-id")
        if pub is not None:
            info["country"] = pub.findtext("country") or "JP"
            info["doc_number"] = pub.findtext("doc-number") or ""
            kind = pub.findtext("kind")
            if kind:
                info["kind"] = kind
            date = pub.findtext("date")
            if date:
                info["publication_date"] = date
            return info if info.get("doc_number") else None

    # Format 3: JP specific (公開番号, 登録番号)
    for tag in ["公開番号", "登録番号", "公表番号"]:
        elem = root.find(f".//{tag}")
        if elem is not None and elem.text:
            # Parse Japanese format: 特開2020-123456
            match = re.match(r"[^\d]*(\d+)", elem.text)
            if match:
                info["country"] = "JP"
                info["doc_number"] = match.group(1)
                if "公開" in tag or "公表" in tag:
                    info["kind"] = "A"
                else:
                    info["kind"] = "B2"
                return info

    return None


def _extract_claims(root: etree._Element) -> list[dict[str, str | int]]:
    """Extract claims from XML."""
    claims: list[dict[str, str | int]] = []

    # Try different claim structures
    # Format 1: claims/claim
    claim_elements = root.findall(".//claims/claim")
    if not claim_elements:
        # Format 2: claim-text directly
        claim_elements = root.findall(".//claim")

    for claim_elem in claim_elements:
        claim_num = claim_elem.get("num") or claim_elem.get("id")
        if claim_num:
            try:
                num = int(re.search(r"\d+", str(claim_num)).group())  # type: ignore
            except (AttributeError, ValueError):
                continue
        else:
            num = len(claims) + 1

        # Get claim text
        claim_text_elem = claim_elem.find(".//claim-text")
        if claim_text_elem is not None:
            raw_text = "".join(claim_text_elem.itertext())
        else:
            raw_text = "".join(claim_elem.itertext())

        raw_text = raw_text.strip()
        normalized_text = normalize_claim_text(raw_text)
        if normalized_text:
            claims.append(
                {
                    "claim_no": num,
                    "claim_text_raw": raw_text,
                    "claim_text_norm": normalized_text,
                    "claim_text": normalized_text,
                }
            )

    # Format 3: Japanese format (請求項)
    if not claims:
        claim_elements = root.findall(".//請求項")
        for i, claim_elem in enumerate(claim_elements, 1):
            raw_text = "".join(claim_elem.itertext()).strip()
            normalized_text = normalize_claim_text(raw_text)
            if normalized_text:
                claims.append(
                    {
                        "claim_no": i,
                        "claim_text_raw": raw_text,
                        "claim_text_norm": normalized_text,
                        "claim_text": normalized_text,
                    }
                )

    return claims


def _extract_specification(root: etree._Element) -> str | None:
    """Extract specification/description text from XML."""
    candidate_paths = [
        ".//description",
        ".//description-of-the-invention",
        ".//detailed-description",
        ".//description-of-embodiments",
        ".//description-of-preferred-embodiments",
        ".//発明の詳細な説明",
        ".//考案の詳細な説明",
    ]

    for path in candidate_paths:
        elem = root.find(path)
        if elem is not None:
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                return text

    # Fallback: scan for tags that look like description sections
    for elem in root.iter():
        tag = elem.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1]
            if "description" in local.lower() or "詳細な説明" in local:
                text = normalize_long_text("".join(elem.itertext()))
                if text and len(text) > 50:
                    return text

    return None


def _extract_spec_sections(
    root: etree._Element,
    specification_text: str | None,
) -> list[dict[str, str]]:
    """Extract specification sections (fallback to a single section)."""
    if not specification_text:
        return []
    return [{"title": "specification", "text": specification_text}]


def _extract_abstract(root: etree._Element) -> str | None:
    """Extract abstract text from XML."""
    candidate_paths = [
        ".//abstract",
        ".//abstract-of-the-disclosure",
        ".//abstract-of-the-invention",
        ".//要約",
    ]
    for path in candidate_paths:
        elem = root.find(path)
        if elem is not None:
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                return text
    return None


def _extract_drawing_description(root: etree._Element) -> str | None:
    """Extract drawing description text from XML."""
    candidate_paths = [
        ".//description-of-drawings",
        ".//drawing-description",
        ".//図面の簡単な説明",
    ]
    for path in candidate_paths:
        elem = root.find(path)
        if elem is not None:
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                return text
    return None


def _extract_abstract(root: etree._Element) -> str | None:
    """Extract abstract/summary text."""
    candidate_paths = [
        ".//abstract",
        ".//summary",
        ".//summary-of-invention",
        ".//要約",
        ".//要約書",
    ]
    for path in candidate_paths:
        elem = root.find(path)
        if elem is not None:
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                return text

    for elem in root.iter():
        tag = elem.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1].lower()
            if local in {"abstract", "summary"} or "要約" in local:
                text = normalize_long_text("".join(elem.itertext()))
                if text:
                    return text
    return None


def _extract_drawing_description(root: etree._Element) -> str | None:
    """Extract brief description of drawings."""
    candidate_paths = [
        ".//brief-description-of-drawings",
        ".//description-of-drawings",
        ".//図面の簡単な説明",
        ".//図面の説明",
    ]
    for path in candidate_paths:
        elem = root.find(path)
        if elem is not None:
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                return text
    for elem in root.iter():
        tag = elem.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1]
            if "drawing" in local.lower() or "図面" in local:
                text = normalize_long_text("".join(elem.itertext()))
                if text and len(text) > 30:
                    return text
    return None


def _extract_spec_sections(
    root: etree._Element,
    specification_text: str | None,
) -> list[dict[str, str]]:
    """Extract specification sections if possible."""
    sections: list[dict[str, str]] = []

    section_paths = [
        ("technical_field", [".//technical-field", ".//技術分野"]),
        ("background", [".//background-art", ".//背景技術"]),
        ("problem", [".//problem-to-be-solved", ".//発明が解決しようとする課題", ".//課題"]),
        ("solution", [".//summary-of-invention", ".//解決手段", ".//課題を解決するための手段"]),
        ("effect", [".//advantageous-effects-of-invention", ".//発明の効果", ".//作用効果"]),
        (
            "embodiments",
            [
                ".//description-of-embodiments",
                ".//description-of-preferred-embodiments",
                ".//実施形態",
            ],
        ),
    ]

    for section_type, paths in section_paths:
        for path in paths:
            elem = root.find(path)
            if elem is None:
                continue
            text = normalize_long_text("".join(elem.itertext()))
            if text:
                sections.append(
                    {
                        "section_type": section_type,
                        "text_raw": text,
                        "text_norm": normalize_long_text(text),
                    }
                )
                break

    if sections:
        return sections

    if specification_text:
        sections = _split_by_bracket_headings(specification_text)
        if sections:
            return sections

    return []


def _split_by_bracket_headings(text: str) -> list[dict[str, str]]:
    """Split specification text by Japanese bracket headings like 【課題】."""
    matches = list(re.finditer(r"【([^】]+)】", text))
    if len(matches) < 2:
        return []

    sections: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        section_type = _classify_section_heading(heading)
        sections.append(
            {
                "section_type": section_type,
                "text_raw": body,
                "text_norm": normalize_long_text(body),
            }
        )
    return sections


def _classify_section_heading(heading: str) -> str:
    """Map heading text to a section_type."""
    if "技術分野" in heading:
        return "technical_field"
    if "背景" in heading:
        return "background"
    if "課題" in heading:
        return "problem"
    if "解決" in heading or "手段" in heading:
        return "solution"
    if "効果" in heading or "作用" in heading:
        return "effect"
    if "実施" in heading:
        return "embodiments"
    if "要約" in heading:
        return "abstract"
    if "図面" in heading:
        return "drawing_description"
    return "other"


def _compute_content_hash(
    claims: list[dict[str, str | int]],
    sections: list[dict[str, str]],
) -> str | None:
    if not claims and not sections:
        return None

    hasher = hashlib.sha256()
    for claim in sorted(claims, key=lambda c: int(c["claim_no"])):
        text = claim.get("claim_text_norm") or claim.get("claim_text_raw") or ""
        hasher.update(f"CLAIM:{claim['claim_no']}\n".encode("utf-8"))
        hasher.update(str(text).encode("utf-8"))
        hasher.update(b"\n")

    for section in sections:
        text = section.get("text_norm") or section.get("text_raw") or ""
        hasher.update(f"SECTION:{section.get('section_type')}\n".encode("utf-8"))
        hasher.update(str(text).encode("utf-8"))
        hasher.update(b"\n")

    return hasher.hexdigest()


def _raw_object_uri(raw_file: RawFile) -> str | None:
    if raw_file.bucket and raw_file.object_path:
        return f"supabase://{raw_file.bucket}/{raw_file.object_path}"
    if raw_file.stored_path.startswith("supabase://"):
        return raw_file.stored_path
    return None


def _load_raw_bytes(raw_file: RawFile) -> bytes | None:
    if raw_file.stored_path:
        local_path = Path(raw_file.stored_path)
        if local_path.exists():
            return local_path.read_bytes()

    object_path = raw_file.object_path
    bucket = raw_file.bucket or settings.supabase_patent_raw_bucket

    if not object_path and raw_file.stored_path.startswith("supabase://"):
        try:
            _, rest = raw_file.stored_path.split("supabase://", 1)
            bucket, object_path = rest.split("/", 1)
        except ValueError:
            object_path = None

    if object_path:
        try:
            storage = SupabaseStorageClient(bucket=bucket)
            return storage.download_bytes(object_path)
        except ValueError as exc:
            logger.error("Supabase download failed", error=str(exc))
            return None

    return None


def parse_single_file(file_id: str) -> dict[str, str]:
    """Parse a single raw file by ID."""
    with get_db() as db:
        raw_file = db.query(RawFile).filter(RawFile.id == file_id).first()
        if not raw_file:
            return {"status": "failed", "message": f"File not found: {file_id}"}

        xml_bytes = _load_raw_bytes(raw_file)
        if not xml_bytes:
            return {"status": "failed", "message": "Raw file not accessible"}

        parsed = parse_jp_gazette_xml_bytes(xml_bytes, origin=str(raw_file.stored_path))
        if not parsed:
            return {"status": "failed", "message": "Could not parse XML"}

        claims = parsed.get("claims", [])
        spec_sections = parsed.get("spec_sections", [])
        abstract_text = parsed.get("abstract_text")
        drawing_description_text = parsed.get("drawing_description_text")
        specification_text = parsed.get("specification_text")

        sections: list[dict[str, str]] = list(spec_sections)
        if abstract_text:
            sections.append(
                {
                    "section_type": "abstract",
                    "text_raw": abstract_text,
                    "text_norm": normalize_long_text(abstract_text),
                }
            )
        if drawing_description_text:
            sections.append(
                {
                    "section_type": "drawing_description",
                    "text_raw": drawing_description_text,
                    "text_norm": normalize_long_text(drawing_description_text),
                }
            )
        if not sections and specification_text:
            sections.append(
                {
                    "section_type": "full",
                    "text_raw": specification_text,
                    "text_norm": normalize_long_text(specification_text),
                }
            )

        # Create or update document
        document = (
            db.query(Document)
            .filter(
                Document.country == parsed["country"],
                Document.doc_number == parsed["doc_number"],
                Document.kind == parsed["kind"],
            )
            .first()
        )

        if not document:
            document = Document(
                country=parsed["country"],
                doc_number=parsed["doc_number"],
                kind=parsed["kind"],
                raw_file_id=raw_file.id,
            )
            db.add(document)
            db.flush()
        else:
            if raw_file.id and not document.raw_file_id:
                document.raw_file_id = raw_file.id

        publication_date = parse_date(parsed.get("publication_date"))
        if publication_date and not document.publication_date:
            document.publication_date = publication_date

        if specification_text:
            existing_text = (
                db.query(DocumentText)
                .filter(
                    DocumentText.document_id == document.id,
                    DocumentText.text_type == "specification",
                    DocumentText.is_current.is_(True),
                )
                .first()
            )
            if existing_text:
                if existing_text.text != specification_text:
                    existing_text.text = specification_text
                    existing_text.source = existing_text.source or "gazette"
                    existing_text.updated_at = datetime.now(timezone.utc)
            else:
                db.add(
                    DocumentText(
                        document_id=document.id,
                        text_type="specification",
                        language="ja",
                        source="gazette",
                        is_current=True,
                        text=specification_text,
                        metadata_json={"raw_file_id": str(raw_file.id)},
                    )
                )

        # Add claims
        for claim_data in claims:
            claim_text = str(claim_data["claim_text_norm"])
            existing_claim = (
                db.query(Claim)
                .filter(
                    Claim.document_id == document.id,
                    Claim.claim_no == claim_data["claim_no"],
                )
                .first()
            )

            if existing_claim:
                existing_claim.claim_text = claim_text
                existing_claim.updated_at = datetime.now(timezone.utc)
                existing_claim.source = existing_claim.source or "gazette"
                existing_claim.is_current = True
            else:
                claim = Claim(
                    document_id=document.id,
                    claim_no=int(claim_data["claim_no"]),
                    claim_text=claim_text,
                    source="gazette",
                    is_current=True,
                )
                db.add(claim)

        # Upsert internal patent identity
        patent = (
            db.query(Patent)
            .filter(
                Patent.jurisdiction == parsed["country"],
                Patent.publication_no == parsed["doc_number"],
            )
            .first()
        )
        if not patent:
            patent = Patent(
                jurisdiction=parsed["country"],
                publication_no=parsed["doc_number"],
            )
            db.add(patent)
            db.flush()

        number_source = (
            db.query(PatentNumberSource)
            .filter(
                PatentNumberSource.internal_patent_id == patent.internal_patent_id,
                PatentNumberSource.number_type == "publication",
                PatentNumberSource.number_value_raw == parsed["doc_number"],
                PatentNumberSource.source_type == "gazette",
            )
            .first()
        )
        if not number_source:
            db.add(
                PatentNumberSource(
                    internal_patent_id=patent.internal_patent_id,
                    number_type="publication",
                    number_value_raw=parsed["doc_number"],
                    number_value_norm=parsed["doc_number"],
                    source_type="gazette",
                    retrieved_at=datetime.now(timezone.utc),
                    confidence=1.0,
                )
            )

        publication_type = "publication"
        kind = (parsed.get("kind") or "").upper()
        if kind.startswith("B"):
            publication_type = "grant"

        content_hash = _compute_content_hash(claims, sections)
        parse_status = "failed"
        if claims and sections:
            parse_status = "succeeded"
        elif claims:
            parse_status = "partial"

        version = None
        if content_hash:
            version = (
                db.query(PatentVersion)
                .filter(
                    PatentVersion.internal_patent_id == patent.internal_patent_id,
                    PatentVersion.publication_type == publication_type,
                    PatentVersion.content_hash == content_hash,
                )
                .first()
            )
        else:
            version = (
                db.query(PatentVersion)
                .filter(
                    PatentVersion.internal_patent_id == patent.internal_patent_id,
                    PatentVersion.publication_type == publication_type,
                    PatentVersion.raw_file_id == raw_file.id,
                )
                .first()
            )

        if not version:
            (
                db.query(PatentVersion)
                .filter(
                    PatentVersion.internal_patent_id == patent.internal_patent_id,
                    PatentVersion.publication_type == publication_type,
                    PatentVersion.is_latest.is_(True),
                )
                .update({"is_latest": False})
            )

            version = PatentVersion(
                internal_patent_id=patent.internal_patent_id,
                publication_type=publication_type,
                kind_code=parsed.get("kind"),
                issue_date=publication_date,
                source_type="gazette",
                raw_file_id=raw_file.id,
                raw_object_uri=_raw_object_uri(raw_file),
                content_hash=content_hash,
                parse_status=parse_status,
                parse_result_json={
                    "claims": len(claims),
                    "sections": len(sections),
                },
                norm_version=NORM_VERSION,
                is_latest=True,
                acquired_at=raw_file.acquired_at,
            )
            db.add(version)
            db.flush()
        else:
            if not version.raw_file_id:
                version.raw_file_id = raw_file.id
            if not version.raw_object_uri:
                version.raw_object_uri = _raw_object_uri(raw_file)
            if not version.parse_status:
                version.parse_status = parse_status
            if not version.parse_result_json:
                version.parse_result_json = {
                    "claims": len(claims),
                    "sections": len(sections),
                }

        if version and version.parse_status != "failed":
            for claim_data in claims:
                existing = (
                    db.query(PatentClaim)
                    .filter(
                        PatentClaim.version_id == version.version_id,
                        PatentClaim.claim_no == claim_data["claim_no"],
                    )
                    .first()
                )
                if existing:
                    existing.text_raw = str(claim_data["claim_text_raw"])
                    existing.text_norm = str(claim_data["claim_text_norm"])
                    existing.norm_version = NORM_VERSION
                else:
                    db.add(
                        PatentClaim(
                            version_id=version.version_id,
                            claim_no=int(claim_data["claim_no"]),
                            text_raw=str(claim_data["claim_text_raw"]),
                            text_norm=str(claim_data["claim_text_norm"]),
                            norm_version=NORM_VERSION,
                        )
                    )

            order_counter: defaultdict[str, int] = defaultdict(int)
            for section in sections:
                section_type = section.get("section_type", "other")
                order_counter[section_type] += 1
                order_no = order_counter[section_type]

                existing = (
                    db.query(PatentSpecSection)
                    .filter(
                        PatentSpecSection.version_id == version.version_id,
                        PatentSpecSection.section_type == section_type,
                        PatentSpecSection.order_no == order_no,
                    )
                    .first()
                )
                if existing:
                    existing.text_raw = section.get("text_raw", "")
                    existing.text_norm = section.get("text_norm")
                    existing.norm_version = NORM_VERSION
                else:
                    db.add(
                        PatentSpecSection(
                            version_id=version.version_id,
                            section_type=section_type,
                            order_no=order_no,
                            text_raw=section.get("text_raw", ""),
                            text_norm=section.get("text_norm"),
                            norm_version=NORM_VERSION,
                        )
                    )

        logger.info(
            "Parsed document",
            doc_number=parsed["doc_number"],
            claims_count=len(claims),
        )
        return {
            "status": "success",
            "message": f"Parsed {len(claims)} claims ({parse_status})",
        }


def parse_pending_files() -> ParseResult:
    """Parse all raw files that haven't been processed yet."""
    result: ParseResult = {"parsed": 0, "failed": 0, "errors": []}

    with get_db() as db:
        # Create parse run
        run = IngestRun(
            run_type="parse",
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(run)
        db.flush()
        run_id = run.id

        # Find raw files without associated documents
        processed_ids = db.query(Document.raw_file_id).filter(
            Document.raw_file_id.isnot(None)
        )
        pending_files = (
            db.query(RawFile)
            .filter(~RawFile.id.in_(processed_ids))
            .all()
        )

    for raw_file in pending_files:
        parse_result = parse_single_file(str(raw_file.id))
        if parse_result["status"] == "success":
            result["parsed"] += 1
        else:
            result["failed"] += 1
            result["errors"].append(f"{raw_file.original_name}: {parse_result['message']}")

    # Update run status
    with get_db() as db:
        run = db.query(IngestRun).filter(IngestRun.id == run_id).first()
        if run:
            run.finished_at = datetime.now(timezone.utc)
            run.status = "completed" if result["failed"] == 0 else "partial"
            run.detail_json = {
                "parsed": result["parsed"],
                "failed": result["failed"],
            }

    return result
