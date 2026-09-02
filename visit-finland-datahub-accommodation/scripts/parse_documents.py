#!/usr/bin/env python3
"""Stage 2: parse uploaded PDF/DOCX documents into normalized, locator-tagged segments.

Never logs document contents -- only counts/lengths/booleans go to stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PAGE_MARKER = re.compile(r"^=== PAGE (\d+) ===$", re.MULTILINE)
PARAGRAPH_MARKER = re.compile(r"^\[PARAGRAPH (\d+)\] (.*)$", re.MULTILINE)
TABLE_MARKER = re.compile(r"^=== TABLE (\d+) ===$", re.MULTILINE)

MIN_CHARS_PER_PAGE_BEFORE_OCR = 10


def parse_pdf(path: Path) -> dict:
    from gaik.software_components.parsers.pymypdf import PyMuPDFParser

    parser = PyMuPDFParser()
    flat = parser.parse_document(str(path), use_markdown=True)
    structured = parser.parse_document(str(path), use_markdown=False)

    structured_text = structured["text_content"]
    markers = list(PAGE_MARKER.finditer(structured_text))
    segments = []
    for idx, m in enumerate(markers):
        start = m.end()
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(structured_text)
        page_no = int(m.group(1))
        page_text = structured_text[start:end].strip()
        segments.append({"locator": f"page {page_no}", "text": page_text})

    page_count = len(markers) if markers else 1
    non_empty_pages = sum(1 for s in segments if len(s["text"]) >= MIN_CHARS_PER_PAGE_BEFORE_OCR)
    ocr_required = page_count > 0 and non_empty_pages == 0

    return {
        "parsing_method": flat["parsing_method"],
        "content_length": flat["content_length"],
        "word_count": flat["word_count"],
        "segments": segments,
        "ocr_required": ocr_required,
        "flat_text": flat["text_content"],
    }


def parse_docx(path: Path) -> dict:
    from gaik.software_components.parsers.docx_parser import DocxParser

    parser = DocxParser()
    flat = parser.parse_document(str(path), use_markdown=True)
    structured = parser.parse_document(str(path), use_markdown=False)

    structured_text = structured["text_content"]
    segments = []
    for m in PARAGRAPH_MARKER.finditer(structured_text):
        para_no, text = m.group(1), m.group(2)
        if text.strip():
            segments.append({"locator": f"paragraph {para_no}", "text": text.strip()})
    for m in TABLE_MARKER.finditer(structured_text):
        table_no = m.group(1)
        segments.append({"locator": f"table {table_no}", "text": f"[table {table_no} content omitted from locator list; see flat_text]"})

    ocr_required = flat["content_length"] == 0

    return {
        "parsing_method": flat["parsing_method"],
        "content_length": flat["content_length"],
        "word_count": flat["word_count"],
        "segments": segments,
        "ocr_required": ocr_required,
        "flat_text": flat["text_content"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    documents_out = []

    for doc in manifest.get("documents", []):
        path = Path(doc["path"])
        ext = path.suffix.lower()
        entry = {
            "id": doc["id"],
            "file_name": path.name,
            "relative_path": doc["relative_path"],
        }
        try:
            if ext == ".pdf":
                parsed = parse_pdf(path)
            elif ext == ".docx":
                parsed = parse_docx(path)
            elif ext == ".doc":
                entry.update({"status": "rejected", "reason": "binary .doc is not accepted"})
                documents_out.append(entry)
                continue
            else:
                entry.update({"status": "rejected", "reason": f"unsupported extension {ext}"})
                documents_out.append(entry)
                continue
        except Exception as exc:  # parser failure must not become a false 'missing'
            entry.update({
                "status": "parse_failed",
                "reason": type(exc).__name__,
                "ocr_required": False,
            })
            documents_out.append(entry)
            continue

        entry.update({
            "status": "parsed",
            "parsing_method": parsed["parsing_method"],
            "content_length": parsed["content_length"],
            "word_count": parsed["word_count"],
            "ocr_required": parsed["ocr_required"],
            "segments": parsed["segments"],
            "flat_text": parsed["flat_text"],
        })
        documents_out.append(entry)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"documents": documents_out}, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "documents_parsed": sum(1 for d in documents_out if d.get("status") == "parsed"),
        "documents_rejected": sum(1 for d in documents_out if d.get("status") == "rejected"),
        "documents_failed": sum(1 for d in documents_out if d.get("status") == "parse_failed"),
        "ocr_required_count": sum(1 for d in documents_out if d.get("ocr_required")),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
