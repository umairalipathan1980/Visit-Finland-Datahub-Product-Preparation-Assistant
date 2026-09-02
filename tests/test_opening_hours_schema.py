import json

import jsonschema
import pytest

from conftest import SCHEMAS_DIR


STRUCTURED_HOURS = {
    "regular": [
        {
            "days": [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
            ],
            "opens": "10:00",
            "closes": "20:00",
        },
        {
            "days": ["sunday"],
            "opens": "10:00",
            "closes": "18:00",
        },
    ]
}


def envelope(status, value=None):
    result = {"status": status}
    if value is not None:
        result["value"] = value
    if status == "found":
        result["evidence"] = [{
            "source_id": "p001",
            "locator": "line 1",
            "excerpt": "Mon-Sat: 10:00-20:00; Sun: 10:00-18:00",
        }]
    return result


def extraction_document(product_type, opening_hours):
    schema_name = f"poc-{product_type}-schema-v1"
    schema = json.loads(
        (SCHEMAS_DIR / f"{product_type}-extraction.schema.json").read_text(encoding="utf-8")
    )
    required = schema["properties"]["fields"]["required"]
    fields = {}
    for name in required:
        if name in {"name", "description"}:
            fields[name] = {"fi": envelope("missing"), "en": envelope("missing")}
        elif name == "images":
            fields[name] = envelope("not_in_scope")
        elif name == "opening_hours":
            fields[name] = envelope("found", opening_hours)
        else:
            fields[name] = envelope("missing")
    return {
        "run_metadata": {
            "schema_name": schema_name,
            "schema_version": "0.2.0-poc",
            "category_taxonomy_version": "poc-subset-0.3",
            "generated_at": "2026-09-02T00:00:00Z",
        },
        "product_type": product_type,
        "fields": fields,
    }


@pytest.mark.parametrize("product_type", ["accommodation", "shops"])
def test_extraction_schema_accepts_structured_opening_hours(product_type):
    schema = json.loads(
        (SCHEMAS_DIR / f"{product_type}-extraction.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker(),
    ).validate(extraction_document(product_type, STRUCTURED_HOURS))


@pytest.mark.parametrize("product_type", ["accommodation", "shops"])
@pytest.mark.parametrize(
    "invalid_value",
    [
        "Mon-Sat 10:00-20:00; Sun 10:00-18:00",
        {"monday_to_saturday": "10:00-20:00", "sunday": "10:00-18:00"},
    ],
)
def test_extraction_schema_rejects_noncanonical_opening_hours(product_type, invalid_value):
    schema = json.loads(
        (SCHEMAS_DIR / f"{product_type}-extraction.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker(),
        ).validate(extraction_document(product_type, invalid_value))


@pytest.mark.parametrize("product_type", ["accommodation", "shops"])
def test_canonical_schema_accepts_same_structured_opening_hours(product_type):
    schema = json.loads(
        (SCHEMAS_DIR / f"canonical-{product_type}.schema.json").read_text(encoding="utf-8")
    )
    document = {
        "run_metadata": {
            "schema_name": f"poc-{product_type}-schema-v1",
            "schema_version": "0.2.0-poc",
            "category_taxonomy_version": "poc-subset-0.3",
            "generated_at": "2026-09-02T00:00:00Z",
        },
        "product_type": product_type,
        "fields": {"opening_hours": STRUCTURED_HOURS},
    }
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker(),
    ).validate(document)


@pytest.mark.parametrize("product_type", ["accommodation", "shops"])
def test_opening_hours_requires_paired_valid_times(product_type):
    invalid = {
        "regular": [{"days": ["monday"], "opens": "9am"}],
    }
    schema = json.loads(
        (SCHEMAS_DIR / f"{product_type}-extraction.schema.json").read_text(encoding="utf-8")
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker(),
        ).validate(extraction_document(product_type, invalid))
