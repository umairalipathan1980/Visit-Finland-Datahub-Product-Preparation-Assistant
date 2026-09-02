"""Deterministic appendix for the otherwise agent-written review report."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DETERMINISTIC_MARKER = "<!-- deterministic-appendix: do not edit -->"


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _markdown(value: Any, limit: int = 180) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _field_envelopes(fields: dict[str, Any]):
    for field_name, value in fields.items():
        if isinstance(value, dict) and "status" in value:
            yield field_name, "", value
        elif isinstance(value, dict):
            for locale, envelope in value.items():
                if isinstance(envelope, dict) and "status" in envelope:
                    yield field_name, locale, envelope


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    rendered = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    rendered.extend("| " + " | ".join(_markdown(cell) for cell in row) + " |" for row in rows)
    if not rows:
        rendered.append("| " + " | ".join(["None", *([""] * (len(headers) - 1))]) + " |")
    return "\n".join(rendered)


def with_deterministic_appendix(
    workspace: Path,
    report: str,
    validation: dict[str, Any],
    bundle_limitations: list[dict[str, Any]],
) -> str:
    report = report.split(DETERMINISTIC_MARKER, 1)[0].rstrip()
    fetched = _read_json(workspace / "work" / "fetched-pages.json", {"pages": [], "failures": []})
    parsed = _read_json(workspace / "work" / "parsed-documents.json", {"documents": []})
    candidates = _read_json(workspace / "work" / "link-candidates.json", {"links": [], "omitted_count": 0})
    scope_decision = _read_json(workspace / "work" / "scope-decision.json", {})
    document_limitations = [
        {"source_id": doc.get("id"), "status": doc.get("status"), "ocr_required": doc.get("ocr_required", False)}
        for doc in parsed.get("documents", [])
        if doc.get("status") != "parsed" or doc.get("ocr_required")
    ]
    result = _read_json(workspace / "work" / "staging-output" / "result.json", {"fields": {}})
    field_rows: list[list[Any]] = []
    evidence_rows: list[list[Any]] = []
    conflict_rows: list[list[Any]] = []
    for field_name, locale, envelope in _field_envelopes(result.get("fields", {})):
        field_rows.append([field_name, locale, envelope.get("status"), envelope.get("value")])
        for evidence in envelope.get("evidence", []):
            evidence_rows.append([
                field_name,
                locale,
                evidence.get("source_id"),
                evidence.get("locator"),
                evidence.get("excerpt"),
            ])
        for alternative in envelope.get("alternatives", []):
            conflict_rows.append([
                field_name,
                locale,
                alternative.get("value"),
                alternative.get("reason"),
            ])
    validation_rows = [
        ["error", item.get("rule_id"), item.get("field"), item.get("message")]
        for item in validation.get("errors", [])
    ] + [
        ["warning", item.get("rule_id"), item.get("field"), item.get("message")]
        for item in validation.get("warnings", [])
    ]
    limitation_count = len(bundle_limitations) + len(document_limitations)
    scope_lines: list[str] = []
    if scope_decision.get("status") == "scope_ambiguous":
        scope_lines = [
            "### Scope review required",
            "",
            f"- Status: `{_markdown(scope_decision.get('status'))}`",
            f"- Error code: `{_markdown(scope_decision.get('error_code'))}`",
            f"- Reason: {_markdown(scope_decision.get('reason') or 'No reason was recorded by an older run.')}",
            f"- Provisional product: {_markdown(scope_decision.get('product'))}",
            f"- Additional candidates: {_markdown(scope_decision.get('additional_products', []))}",
            "- Extraction continued conservatively; scope-dependent fields must be reviewed.",
            "",
        ]
    appendix = "\n".join([
        DETERMINISTIC_MARKER,
        "## Deterministic retrieval and validation summary",
        "",
        f"- Stored website pages: {len(fetched.get('pages', []))}",
        f"- Page retrieval failures: {len(fetched.get('failures', []))}",
        f"- Documents declared: {len(parsed.get('documents', []))}",
        f"- Document/OCR limitations: {len(document_limitations)}",
        f"- Candidate links indexed: {len(candidates.get('links', []))}",
        f"- Candidate links omitted from the agent inventory: {candidates.get('omitted_count', 0)}",
        f"- Evidence-bundle truncation/omission events: {len(bundle_limitations)}",
        f"- Validation errors: {len(validation.get('errors', []))}",
        f"- Validation warnings: {len(validation.get('warnings', []))}",
        "",
        *scope_lines,
        "### Field status table",
        "",
        _table(["Field", "Locale", "Status", "Value"], field_rows),
        "",
        "### Evidence table",
        "",
        _table(["Field", "Locale", "Source", "Locator", "Excerpt"], evidence_rows),
        "",
        "### Conflict table",
        "",
        _table(["Field", "Locale", "Alternative", "Reason"], conflict_rows),
        "",
        "### Validation table",
        "",
        _table(["Severity", "Rule", "Field", "Message"], validation_rows),
    ])
    if limitation_count:
        appendix += "\n\nRetrieval limitations were detected; missing fields must not be interpreted as facts absent from the source site."
    return report.rstrip() + "\n\n" + appendix + "\n"
