"""Template: normalize raw patent data into JP Patent Index JSONL.

This script is a starter template. Adjust mapping logic to match the actual
bulk data format once received.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Map raw record to normalized JSONL schema."""
    application_number = raw.get("application_number") or raw.get("出願番号")
    filing_date = raw.get("filing_date") or raw.get("出願日")
    title = raw.get("title") or raw.get("発明の名称")
    abstract = raw.get("abstract") or raw.get("要約")
    last_update_date = raw.get("last_update_date") or raw.get("更新日")

    documents = raw.get("documents") or []
    if not documents:
        publication_number = raw.get("publication_number") or raw.get("公開番号")
        patent_number = raw.get("patent_number") or raw.get("特許番号")
        kind = raw.get("kind")
        publication_date = raw.get("publication_date") or raw.get("公開日")
        if publication_number or patent_number:
            documents = [
                {
                    "doc_type": "publication" if publication_number else "registration",
                    "publication_number": publication_number,
                    "patent_number": patent_number,
                    "kind": kind,
                    "publication_date": publication_date,
                }
            ]

    applicants = raw.get("applicants") or []
    if not applicants:
        applicant_raw = raw.get("applicant") or raw.get("出願人")
        if applicant_raw:
            applicants = [{"name_raw": applicant_raw, "role": "applicant", "is_primary": True}]

    classifications = raw.get("classifications") or []
    if not classifications:
        ipc_codes = raw.get("ipc") or raw.get("IPC")
        if ipc_codes:
            if isinstance(ipc_codes, str):
                ipc_codes = [c.strip() for c in ipc_codes.split(";") if c.strip()]
            classifications = [{"type": "IPC", "code": code} for code in ipc_codes]

    status_events = raw.get("status_events") or []
    if not status_events:
        status = raw.get("status") or raw.get("権利状態")
        status_date = raw.get("status_date") or raw.get("状態日")
        if status:
            status_events = [
                {"event_type": str(status).upper(), "event_date": status_date}
            ]

    return {
        "application_number": application_number,
        "filing_date": filing_date,
        "title": title,
        "abstract": abstract,
        "last_update_date": last_update_date,
        "documents": documents,
        "applicants": applicants,
        "classifications": classifications,
        "status_events": status_events,
    }


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def iter_json(path: Path) -> Iterable[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        yield from data
    elif isinstance(data, dict):
        yield data


def iter_csv(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def detect_records(path: Path) -> Iterable[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return iter_jsonl(path)
    if suffix == ".json":
        return iter_json(path)
    if suffix == ".csv":
        return iter_csv(path)
    raise ValueError(f"Unsupported input format: {suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize JP patent raw data to JSONL")
    parser.add_argument("--input", required=True, help="Input file (json/jsonl/csv)")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    records = detect_records(input_path)

    with output_path.open("w", encoding="utf-8") as out:
        for raw in records:
            normalized = normalize_record(raw)
            out.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    print(f"Normalized JSONL written: {output_path}")


if __name__ == "__main__":
    main()
