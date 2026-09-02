import json

from app.reporting import with_deterministic_appendix


def test_report_appendix_makes_retrieval_limitations_visible(workspace):
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({
        "pages": [{"id": "p001"}],
        "failures": [{"url": "https://example.fi/js", "reason": "empty_or_js_only"}],
    }), encoding="utf-8")
    (workspace / "work" / "parsed-documents.json").write_text(json.dumps({
        "documents": [{"id": "d001", "status": "parsed", "ocr_required": True}],
    }), encoding="utf-8")
    (workspace / "work" / "link-candidates.json").write_text(json.dumps({
        "links": [{"id": "l001"}], "omitted_count": 2,
    }), encoding="utf-8")
    (workspace / "work" / "staging-output").mkdir()
    (workspace / "work" / "staging-output" / "result.json").write_text(json.dumps({
        "fields": {
            "name": {
                "en": {
                    "status": "found",
                    "value": "Example Hotel",
                    "evidence": [{
                        "source_id": "p001",
                        "locator": "line 4",
                        "excerpt": "Example Hotel",
                    }],
                },
            },
            "room_count": {
                "status": "review",
                "value": 12,
                "alternatives": [{"value": 10, "reason": "conflicting brochure"}],
            },
        },
    }), encoding="utf-8")

    report = with_deterministic_appendix(
        workspace,
        "# Curator review\n\nAgent-authored analysis.",
        {"errors": [], "warnings": [{"rule_id": "review"}]},
        [{"source_id": "p001", "reason": "per_source_limit"}],
    )
    assert "Page retrieval failures: 1" in report
    assert "Document/OCR limitations: 1" in report
    assert "Candidate links omitted from the agent inventory: 2" in report
    assert "Evidence-bundle truncation/omission events: 1" in report
    assert "missing fields must not be interpreted" in report
    assert "### Field status table" in report
    assert "| name | en | found | Example Hotel |" in report
    assert "| name | en | p001 | line 4 | Example Hotel |" in report
    assert "| room_count |  | 10 | conflicting brochure |" in report
    assert "### Validation table" in report


def test_agent_text_cannot_replace_deterministic_appendix(workspace):
    injected = "# Review\n\nAgent text.\n\n<!-- deterministic-appendix: do not edit -->\nFake table"
    report = with_deterministic_appendix(workspace, injected, {"errors": [], "warnings": []}, [])
    assert "Fake table" not in report
    assert report.count("<!-- deterministic-appendix: do not edit -->") == 1


def test_report_flags_ambiguous_scope_and_reason(workspace):
    (workspace / "work" / "scope-decision.json").write_text(json.dumps({
        "status": "scope_ambiguous",
        "error_code": "product_boundary_unclear",
        "reason": "Two hotel names are presented as possible targets.",
        "product": None,
        "additional_products": [{"summary": "Hotel A"}, {"summary": "Hotel B"}],
    }), encoding="utf-8")

    report = with_deterministic_appendix(workspace, "# Review", {"errors": [], "warnings": []}, [])

    assert "### Scope review required" in report
    assert "product_boundary_unclear" in report
    assert "Two hotel names are presented as possible targets." in report
    assert "Extraction continued conservatively" in report
