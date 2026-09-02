#!/usr/bin/env python3
"""Stage 1: validate request.json and establish approved source/domain boundaries."""
from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import jsonschema

ALLOWED_DOC_EXTENSIONS = {".pdf", ".docx"}
PRIVATE_HOST_LABELS = {"localhost"}


def _err(code: str, message: str, **extra) -> dict:
    return {"error_code": code, "message": message, **extra}


def _fail(code: str, message: str, **extra) -> None:
    print(json.dumps(_err(code, message, **extra)), file=sys.stderr)
    sys.exit(1)


def registrable_domain(host: str) -> str:
    """Best-effort registrable-domain heuristic (last two labels).

    This is a PoC simplification, not a public-suffix-list implementation;
    it is adequate for the plain .fi/.com-style domains this release targets
    and is documented as a limitation rather than silently assumed correct.
    """
    labels = host.lower().rstrip(".").split(".")
    if len(labels) <= 2:
        return ".".join(labels)
    return ".".join(labels[-2:])


def is_private_or_unsafe_host(host: str) -> bool:
    host_l = host.lower()
    if host_l in PRIVATE_HOST_LABELS:
        return True
    try:
        addrs = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return True  # cannot resolve -> refuse rather than guess
    for addr in addrs:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return True
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or str(ip) == "169.254.169.254"  # cloud metadata endpoint
        ):
            return True
    return False


def validate_url(raw_url: str) -> dict:
    parsed = urlparse(raw_url)
    if parsed.scheme not in ("http", "https"):
        _fail("unsupported_scheme", f"URL scheme must be http/https: {raw_url}")
    if not parsed.hostname:
        _fail("invalid_url", f"URL has no host: {raw_url}")
    if is_private_or_unsafe_host(parsed.hostname):
        _fail("unsafe_host", f"URL host is private/unresolvable/unsafe: {raw_url}")
    return {
        "url": raw_url,
        "host": parsed.hostname.lower(),
        "registrable_domain": registrable_domain(parsed.hostname),
    }


def validate_document_path(doc_rel_path: str, input_dir: Path, documents_dir: Path) -> Path:
    """`doc_rel_path` is relative to input/ and already includes the
    'documents/' prefix (per the request contract example in Section 5), so
    it is joined against input_dir, not against documents_dir -- joining
    against documents_dir a second time would double that prefix."""
    candidate = (input_dir / doc_rel_path).resolve()
    try:
        candidate.relative_to(documents_dir.resolve())
    except ValueError:
        _fail("path_traversal", f"document path escapes input/documents: {doc_rel_path}")
    if candidate.suffix.lower() not in ALLOWED_DOC_EXTENSIONS:
        _fail("unsupported_file_type", f"unsupported document type: {doc_rel_path}")
    if not candidate.is_file():
        _fail("file_not_found", f"document not found: {doc_rel_path}")
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    input_path = Path(args.input)
    schema_path = Path(args.schema)
    output_path = Path(args.output)

    try:
        request = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail("request_unreadable", f"could not read/parse request.json: {exc}")
        return 1  # unreachable, satisfies type checkers

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(request), key=lambda e: list(e.path))
    if errors:
        details = [{"path": list(e.path), "message": e.message} for e in errors]
        _fail("contract_validation_failed", "request.json does not satisfy contract_version v1", errors=details)
        return 1

    input_dir = input_path.parent
    documents_dir = input_dir / "documents"

    sources = []
    approved_domains = set()
    for i, url in enumerate(request["website_urls"], start=1):
        info = validate_url(url)
        source_id = f"p{i:03d}"
        sources.append({"id": source_id, "type": "seed_url", **info})
        approved_domains.add(info["registrable_domain"])

    documents = []
    for j, doc_rel in enumerate(request.get("document_files", []), start=1):
        resolved = validate_document_path(doc_rel, input_dir, documents_dir)
        documents.append({
            "id": f"d{j:03d}",
            "type": "document",
            "path": str(resolved),
            "relative_path": doc_rel,
        })

    manifest = {
        "contract_version": request["contract_version"],
        "product_type": request["product_type"],
        "languages": request.get("languages", ["fi", "en"]),
        "sources": sources,
        "approved_domains": sorted(approved_domains),
        "documents": documents,
        "next_source_id_index": len(sources) + 1,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "sources": len(sources), "documents": len(documents)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
