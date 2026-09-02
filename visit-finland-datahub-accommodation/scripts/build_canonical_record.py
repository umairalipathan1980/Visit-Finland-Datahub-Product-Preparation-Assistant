#!/usr/bin/env python3
"""Stage 7: build the provisional canonical record from unambiguous 'found' values only."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

LOCALIZED_FIELDS = {"name", "description"}


def extract_value(field_name: str, envelope_or_locales):
    if field_name in LOCALIZED_FIELDS:
        out = {}
        for locale, envelope in envelope_or_locales.items():
            if envelope.get("status") == "found":
                out[locale] = envelope["value"]
        return out or None
    envelope = envelope_or_locales
    if envelope.get("status") == "found":
        return envelope["value"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    result = json.loads(Path(args.input).read_text(encoding="utf-8"))

    fields_out = {}
    for name, envelope_or_locales in result["fields"].items():
        if name == "images":
            continue  # not_in_scope, never included
        value = extract_value(name, envelope_or_locales)
        if value is not None:
            fields_out[name] = value

    canonical = {
        "run_metadata": {
            **result["run_metadata"],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "product_type": result["product_type"],
        "fields": fields_out,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(canonical, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "fields_included": len(fields_out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
