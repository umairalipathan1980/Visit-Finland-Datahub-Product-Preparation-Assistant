#!/usr/bin/env python3
"""Stage 6: deterministic JSON Schema + DataHub-specific validation.

Quote verification is the primary anti-fabrication control: every 'found'
value's evidence excerpts must occur literally (after whitespace/quote
normalization) in the stored source artifact they cite. An excerpt that
cannot be located is downgraded to 'review' with rule_id quote_not_verified.

Reports success against the selected local PoC product schema, never as
DataHub-valid.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema

WHITESPACE_RE = re.compile(r"\s+")
QUOTE_CHARS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
}
MAX_RECOMMENDED_CATEGORIES = 5


def normalize_for_quote_check(text: str) -> str:
    for a, b in QUOTE_CHARS.items():
        text = text.replace(a, b)
    return WHITESPACE_RE.sub(" ", text).strip()


def load_source_text(workspace: Path, source_id: str, parsed_documents: dict) -> str | None:
    page_path = workspace / "work" / "pages" / f"{source_id}.txt"
    if page_path.is_file():
        return page_path.read_text(encoding="utf-8")
    for doc in parsed_documents.get("documents", []):
        if doc.get("id") == source_id:
            return doc.get("flat_text", "")
    return None


def verify_quote(excerpt: str, source_text: str | None) -> bool:
    if source_text is None:
        return False
    return normalize_for_quote_check(excerpt) in normalize_for_quote_check(source_text)


def iter_field_envelopes(fields: dict):
    for name, value in fields.items():
        if isinstance(value, dict) and "status" in value:
            yield name, None, value
        elif isinstance(value, dict):
            for locale, envelope in value.items():
                if isinstance(envelope, dict) and "status" in envelope:
                    yield name, locale, envelope


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    # Per the plan's own reasoning for the Bash argv contract (Section 9), every
    # path this script needs beyond --input/--schema/--output is a constant it
    # can compute itself: the workspace root is --input's grandparent
    # (<workspace>/work/extraction-draft.json), and the taxonomy/provenance
    # files are fixed package-relative paths. Neither is a CLI flag, so there
    # is nothing there for a hostile invocation to redirect.
    input_path = Path(args.input).resolve()
    workspace = input_path.parents[1]
    package_dir = Path(__file__).resolve().parent.parent
    categories_path = package_dir / "schemas" / "datahub-categories.json"
    draft = json.loads(input_path.read_text(encoding="utf-8"))
    product_type = draft.get("product_type")
    version_file = "shops-schema-version.json" if product_type == "shops" else "schema-version.json"
    schema_version_path = package_dir / "schemas" / version_file

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    categories_doc = json.loads(categories_path.read_text(encoding="utf-8"))
    schema_version_doc = json.loads(schema_version_path.read_text(encoding="utf-8"))

    parsed_documents_path = workspace / "work" / "parsed-documents.json"
    parsed_documents = (
        json.loads(parsed_documents_path.read_text(encoding="utf-8"))
        if parsed_documents_path.is_file() else {"documents": []}
    )

    errors: list[dict] = []
    warnings: list[dict] = []

    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(draft), key=lambda e: list(e.path))
    for e in schema_errors:
        errors.append({"rule_id": "schema_violation", "path": list(e.path), "message": e.message})

    if not schema_errors:
        fields = draft["fields"]

        # Quote verification: downgrade unverified 'found' excerpts to 'review'.
        for field_name, locale, envelope in iter_field_envelopes(fields):
            if envelope.get("status") != "found":
                continue
            all_verified = True
            for ev in envelope.get("evidence", []):
                source_text = load_source_text(workspace, ev["source_id"], parsed_documents)
                verified = verify_quote(ev["excerpt"], source_text)
                ev["quote_verified"] = verified
                if not verified:
                    all_verified = False
            if not all_verified:
                envelope["status"] = "review"
                envelope["notes"] = (envelope.get("notes", "") + " quote_not_verified").strip()
                warnings.append({
                    "rule_id": "quote_not_verified",
                    "field": field_name, "locale": locale,
                    "message": "one or more evidence excerpts could not be verified against stored source text; downgraded to review",
                })

        # Accessibility / STF (invariant 7) are never inferred. This has no
        # dedicated check here because the schema's fieldEnvelope already
        # requires non-empty evidence whenever status is "found" -- a
        # found-without-evidence accessibility value is a schema_violation
        # before this function's custom rules ever run, for every field, not
        # just these two. Quote verification above is what catches an
        # accessibility value backed by a fabricated excerpt.

        # Category assignment is classification, not extraction (plan Section 7):
        # a category is never accepted as 'found', regardless of taxonomy match.
        categories_envelope = fields.get("categories", {})
        if categories_envelope.get("status") == "found":
            categories_envelope["status"] = "review"
            warnings.append({
                "rule_id": "category_is_classification",
                "message": "category assignment is a classification judgment, not a verbatim extraction; "
                           "downgraded from found to review unconditionally, regardless of taxonomy match",
            })

        if categories_envelope.get("status") == "review":
            category_prefix = f"{product_type}."
            known_ids = {
                c["id"] for c in categories_doc["categories"]
                if c["id"].startswith(category_prefix)
            }
            values = categories_envelope.get("value") or []
            unknown = [v for v in values if v not in known_ids]
            if unknown:
                warnings.append({"rule_id": "unknown_category", "values": unknown,
                                   "message": f"category id is not valid for the selected {product_type} product taxonomy"})
            if len(values) > MAX_RECOMMENDED_CATEGORIES:
                warnings.append({"rule_id": "max_five_categories", "count": len(values),
                                   "message": "more than five categories selected; DataHub guidance recommends five, severity is provisional"})

        # Images always not_in_scope, never carries evidence.
        images_envelope = fields.get("images", {})
        if images_envelope.get("status") != "not_in_scope":
            errors.append({"rule_id": "images_out_of_scope", "message": "images must be status not_in_scope for this PoC"})

    result = dict(draft)
    result["validation"] = {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
    result["run_metadata"] = {
        **result.get("run_metadata", {}),
        "schema_name": schema_version_doc["schema_name"],
        "schema_version": schema_version_doc["schema_version"],
        "category_taxonomy_version": categories_doc["taxonomy_version"],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": f"valid_against_{schema_version_doc['schema_name']}" if not errors else "invalid",
        "error_count": len(errors),
        "warning_count": len(warnings),
    }))
    return 0 if not errors else 4


if __name__ == "__main__":
    sys.exit(main())
