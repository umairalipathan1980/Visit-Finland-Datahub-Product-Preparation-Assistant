import json
import subprocess
import sys

from conftest import SCHEMAS_DIR, SCRIPTS_DIR


def run_validate_extraction(workspace):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_extraction.py"),
         "--input", str(workspace / "work" / "extraction-draft.json"),
         "--schema", str(SCHEMAS_DIR / "accommodation-extraction.schema.json"),
         "--output", str(workspace / "work" / "staging-output" / "result.json")],
        capture_output=True, text=True,
    )


def envelope(status, value=None, evidence=None):
    e = {"status": status}
    if value is not None:
        e["value"] = value
    if evidence is not None:
        e["evidence"] = evidence
    return e


def minimal_draft(**field_overrides):
    fields = {
        "name": {"fi": envelope("missing"), "en": envelope("missing")},
        "description": {"fi": envelope("missing"), "en": envelope("missing")},
        "address": envelope("missing"),
        "coordinates": envelope("missing"),
        "contact": envelope("missing"),
        "categories": envelope("missing"),
        "accessibility": envelope("missing"),
        "sustainability_label": envelope("missing"),
        "stf_status": envelope("missing"),
        "capacity": envelope("missing"),
        "pricing": envelope("missing"),
        "booking_url": envelope("missing"),
        "availability": envelope("missing"),
        "opening_hours": envelope("missing"),
        "amenities": envelope("missing"),
        "languages_spoken": envelope("missing"),
        "images": envelope("not_in_scope"),
    }
    fields.update(field_overrides)
    return {
        "run_metadata": {
            "schema_name": "poc-accommodation-schema-v1", "schema_version": "x",
            "category_taxonomy_version": "x", "generated_at": "2026-01-01T00:00:00Z",
        },
        "product_type": "accommodation",
        "fields": fields,
    }


def write_draft(workspace, draft):
    (workspace / "work" / "extraction-draft.json").write_text(json.dumps(draft), encoding="utf-8")


def test_fabricated_excerpt_is_downgraded_to_review(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("Tervetuloa hotelliin. 42 huonetta.", encoding="utf-8")
    draft = minimal_draft(capacity=envelope("found", {"rooms": 42}, [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "this text does not appear on the page"}
    ]))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["capacity"]["status"] == "review"
    assert any(w["rule_id"] == "quote_not_verified" for w in output["validation"]["warnings"])


def test_verified_excerpt_stays_found(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("Tervetuloa hotelliin. 42 huonetta.", encoding="utf-8")
    draft = minimal_draft(capacity=envelope("found", {"rooms": 42}, [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "42 huonetta"}
    ]))
    write_draft(workspace, draft)
    run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["capacity"]["status"] == "found"
    assert output["fields"]["capacity"]["evidence"][0]["quote_verified"] is True


def test_found_category_is_always_downgraded_to_review_even_when_valid(workspace):
    """Category assignment is classification, not extraction: a perfectly
    known, valid category must still never survive as 'found'."""
    (workspace / "work" / "pages" / "p001.txt").write_text("Tämä on hotelli keskustassa.", encoding="utf-8")
    draft = minimal_draft(categories=envelope("found", ["accommodation.hotel"], [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "Tämä on hotelli keskustassa."}
    ]))
    write_draft(workspace, draft)
    run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["categories"]["status"] == "review"
    assert any(w["rule_id"] == "category_is_classification" for w in output["validation"]["warnings"])


def test_unknown_category_is_a_warning_not_an_error(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("Tämä on ihan uudenlainen majoitusmuoto.", encoding="utf-8")
    draft = minimal_draft(categories=envelope("review", ["accommodation.not_a_real_category"], [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "Tämä on ihan uudenlainen majoitusmuoto."}
    ]))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["categories"]["status"] == "review"
    assert any(w["rule_id"] == "unknown_category" for w in output["validation"]["warnings"])
    assert not any(e["rule_id"] == "unknown_category" for e in output["validation"]["errors"])
    assert result.returncode == 0


def test_missing_categories_never_fails_validation(workspace):
    draft = minimal_draft(categories=envelope("missing"))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 0
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["validation"]["valid"] is True


def test_more_than_five_categories_warns(workspace):
    ids = ["accommodation.hotel", "accommodation.hostel", "accommodation.bed_and_breakfast",
           "accommodation.cottage", "accommodation.camping", "accommodation.glamping"]
    (workspace / "work" / "pages" / "p001.txt").write_text(" ".join(ids), encoding="utf-8")
    draft = minimal_draft(categories=envelope("review", ids, [
        {"source_id": "p001", "locator": "https://x/", "excerpt": " ".join(ids)}
    ]))
    write_draft(workspace, draft)
    run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert any(w["rule_id"] == "max_five_categories" for w in output["validation"]["warnings"])


def test_accessibility_found_without_evidence_is_a_schema_violation(workspace):
    """Invariant 7 (never inferred) is enforced structurally: fieldEnvelope
    requires non-empty evidence for every 'found' field, accessibility included."""
    draft = minimal_draft(accessibility={"status": "found", "value": "accessible"})
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 4
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert any(e["rule_id"] == "schema_violation" for e in output["validation"]["errors"])


def test_availability_found_with_evidence_passes(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("Avoinna ympäri vuoden, min. 1 yö.", encoding="utf-8")
    draft = minimal_draft(availability=envelope("found", {"open_year_round": True, "minimum_stay_nights": 1}, [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "Avoinna ympäri vuoden, min. 1 yö."}
    ]))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 0
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["availability"]["status"] == "found"


def test_missing_availability_never_fails_validation(workspace):
    draft = minimal_draft(availability=envelope("missing"))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 0


def test_booking_url_to_a_third_party_domain_is_quote_verifiable(workspace):
    """The stored page text includes an appended Links section (fetch_pages.py),
    so a booking_url pointing at an off-domain booking engine is still
    citable evidence from the approved page that links to it -- without ever
    fetching or citing the booking engine's own content."""
    stored_page_text = (
        "Varaa majoituksesi helposti verkossa.\n\n"
        "--- LINKS ---\n"
        "Varaa nyt -> https://villamaija.guestybookings.com/en\n"
    )
    (workspace / "work" / "pages" / "p001.txt").write_text(stored_page_text, encoding="utf-8")
    draft = minimal_draft(booking_url=envelope("found", "https://villamaija.guestybookings.com/en", [
        {"source_id": "p001", "locator": "https://x/", "excerpt": "Varaa nyt -> https://villamaija.guestybookings.com/en"}
    ]))
    write_draft(workspace, draft)
    run_validate_extraction(workspace)
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert output["fields"]["booking_url"]["status"] == "found"
    assert output["fields"]["booking_url"]["evidence"][0]["quote_verified"] is True


def test_images_not_not_in_scope_is_an_error(workspace):
    draft = minimal_draft(images=envelope("missing"))
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 4


def test_schema_violation_is_reported(workspace):
    draft = minimal_draft()
    del draft["fields"]["name"]
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 4
    output = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
    assert any(e["rule_id"] == "schema_violation" for e in output["validation"]["errors"])


def test_success_reports_poc_schema_not_datahub_valid(workspace):
    draft = minimal_draft()
    write_draft(workspace, draft)
    result = run_validate_extraction(workspace)
    assert result.returncode == 0
    assert "poc-accommodation-schema-v1" in result.stdout
    assert "DataHub-valid" not in result.stdout
