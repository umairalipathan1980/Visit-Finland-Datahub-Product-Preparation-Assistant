#!/usr/bin/env python3
"""Stage 7: native .xlsx export via openpyxl.

Stable one-row columns with .fi/.en suffixes, deterministic array
serialization, fixed sheet name/column order, and formula-injection
protection -- a value beginning with =, +, -, or @ is written as text.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openpyxl import Workbook

SHEET_NAMES = {"accommodation": "Accommodation", "shops": "Shops"}

# Fixed column order. Localized fields expand to two columns; status columns
# ride alongside their value column so a curator can see why something is
# blank without opening result.json.
COMMON_COLUMNS = [
    ("name.fi", "name", "fi"), ("name.en", "name", "en"),
    ("description.fi", "description", "fi"), ("description.en", "description", "en"),
    ("address", "address", None),
    ("coordinates", "coordinates", None),
    ("contact", "contact", None),
    ("categories", "categories", None),
    ("accessibility", "accessibility", None),
    ("sustainability_label", "sustainability_label", None),
    ("stf_status", "stf_status", None),
    ("opening_hours", "opening_hours", None),
    ("languages_spoken", "languages_spoken", None),
]

ACCOMMODATION_ONLY_COLUMNS = [
    ("capacity", "capacity", None),
    ("pricing", "pricing", None),
    ("booking_url", "booking_url", None),
    ("availability", "availability", None),
    ("amenities", "amenities", None),
]

FORMULA_PREFIXES = ("=", "+", "-", "@")


def neutralize(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def serialize_value(value):
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return neutralize(", ".join(str(v) for v in value))
    if isinstance(value, dict):
        return neutralize(json.dumps(value, sort_keys=True, ensure_ascii=False))
    return neutralize(str(value))


def field_value(fields: dict, field_name: str, locale: str | None):
    envelope_or_locales = fields.get(field_name, {})
    if locale is not None:
        envelope = envelope_or_locales.get(locale, {})
    else:
        envelope = envelope_or_locales
    if envelope.get("status") != "found":
        return None
    return envelope.get("value")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    result = json.loads(Path(args.input).read_text(encoding="utf-8"))
    fields = result["fields"]
    product_type = result.get("product_type", "accommodation")
    if product_type not in SHEET_NAMES:
        raise ValueError(f"unsupported product_type: {product_type}")
    columns = COMMON_COLUMNS + (
        ACCOMMODATION_ONLY_COLUMNS if product_type == "accommodation" else []
    )

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAMES[product_type]
    ws.append([col_name for col_name, _, _ in columns])
    ws.append([serialize_value(field_value(fields, field_name, locale)) for _, field_name, locale in columns])

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(json.dumps({"status": "ok", "columns": len(columns), "product_type": product_type}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
