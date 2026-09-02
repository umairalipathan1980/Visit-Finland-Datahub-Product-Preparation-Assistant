import json
from pathlib import Path

import pytest
from openpyxl import Workbook

import app.agent_tools as agent_tools
from app.telemetry import RunTelemetry
from conftest import PACKAGE_DIR


def _payload(response):
    return json.loads(response["content"][0]["text"])


@pytest.mark.asyncio
async def test_complete_coarse_tool_sequence_uses_empty_document_fast_path(workspace, monkeypatch):
    calls = []

    async def fake_run_script(state, script_name, *args):
        calls.append(script_name)
        values = {args[index]: Path(args[index + 1]) for index in range(0, len(args), 2) if args[index].startswith("--") and index + 1 < len(args)}
        if script_name == "validate_source_manifest_optimized.py":
            agent_tools._write_json_atomic(values["--output"], {
                "contract_version": "v1", "product_type": "accommodation", "languages": ["fi", "en"],
                "sources": [{"id": "p001", "type": "seed_url", "url": "https://example.fi/"}],
                "approved_domains": ["example.fi"], "documents": [], "next_source_id_index": 2,
            })
            return {"returncode": 0, "result": {"status": "ok", "sources": 1, "documents": 0}, "error": None}
        if script_name == "fetch_pages_optimized.py":
            pages_dir = values["--pages-dir"]
            pages_dir.mkdir(parents=True, exist_ok=True)
            text = "Example Hotel has 12 rooms in Helsinki and offers a sauna."
            (pages_dir / "p001.txt").write_text(text, encoding="utf-8")
            agent_tools._write_json_atomic(pages_dir / "p001.meta.json", {
                "source_id": "p001", "url": "https://example.fi/", "final_url": "https://example.fi/",
                "internal_link_details": [{"text": "Contact", "href": "https://example.fi/contact"}],
                "external_link_details": [],
            })
            agent_tools._write_json_atomic(values["--output"], {
                "pages": [{"id": "p001", "url": "https://example.fi/", "final_url": "https://example.fi/",
                           "http_status": 200, "content_hash": "abc", "canonical_url": None}],
                "failures": [], "next_source_id_index": 2,
            })
            return {"returncode": 0, "result": {"status": "ok", "fetched": 1, "failures": 0, "total_pages": 1}, "error": None}
        if script_name == "validate_extraction.py":
            draft = json.loads(values["--input"].read_text(encoding="utf-8"))
            draft["validation"] = {"valid": True, "errors": [], "warnings": []}
            agent_tools._write_json_atomic(values["--output"], draft)
            return {"returncode": 0, "result": {"status": "valid", "error_count": 0, "warning_count": 0}, "error": None}
        if script_name == "build_canonical_record.py":
            result = json.loads((workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8"))
            agent_tools._write_json_atomic(values["--output"], {
                "run_metadata": result["run_metadata"],
                "product_type": "accommodation",
                "fields": {},
            })
            return {"returncode": 0, "result": {"status": "ok"}, "error": None}
        if script_name == "export_xlsx.py":
            workbook = Workbook()
            workbook.save(values["--output"])
            return {"returncode": 0, "result": {"status": "ok"}, "error": None}
        raise AssertionError(f"unexpected script {script_name}")

    monkeypatch.setattr(agent_tools, "_run_script", fake_run_script)
    (workspace / "input" / "request.json").write_text(json.dumps({
        "contract_version": "v1", "product_type": "accommodation",
        "website_urls": ["https://example.fi/"], "document_files": [],
    }), encoding="utf-8")
    telemetry = RunTelemetry("test")
    _server, state, _allowed = agent_tools.build_optimized_tool_server(workspace, PACKAGE_DIR, telemetry)

    assert _payload(await state.handlers["load_skill"]({}))["status"] == "ok"
    prepared = _payload(await state.handlers["prepare_sources"]({}))
    assert prepared["status"] == "ok"
    assert prepared["candidate_count"] == 1
    assert prepared["next_action"]["tool"] == "read_context_page"
    assert "parse_documents.py" not in calls
    assert json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8")) == {"documents": []}

    context = _payload(await state.handlers["read_context_page"]({"cursor": prepared["next_context_cursor"]}))
    assert context["candidate_links"][0]["id"] == "l001"
    assert context["evidence"][0]["text"] == "Example Hotel has 12 rooms in Helsinki and offers a sauna."
    assert context["context_complete"] is True

    repeated_prepare = _payload(await state.handlers["prepare_sources"]({}))
    assert repeated_prepare["idempotent"] is True
    assert repeated_prepare["next_action"]["tool"] == "fetch_selected_pages_or_record_scope"
    assert "evidence" not in repeated_prepare
    assert calls.count("fetch_pages_optimized.py") == 1

    scope = await state.handlers["record_scope"]({"scope_decision": {
        "status": "resolved", "error_code": None,
        "product": {"pages": ["p001"], "summary": "one hotel"},
        "excluded": [], "additional_products": [], "out_of_type_facilities": [],
    }})
    assert scope["is_error"] is False

    localized_missing = {
        "fi": {"status": "missing"},
        "en": {"status": "missing"},
    }
    fields = {
        "name": localized_missing,
        "description": localized_missing,
        **{
            name: {"status": "not_in_scope"} if name == "images" else {"status": "missing"}
            for name in (
                "address", "coordinates", "contact", "categories", "accessibility",
                "sustainability_label", "stf_status", "capacity", "pricing",
                "booking_url", "availability", "opening_hours", "amenities",
                "languages_spoken", "images",
            )
        },
    }
    extraction = {
        "run_metadata": {
            "schema_name": "poc-accommodation-schema-v1", "schema_version": "test",
            "category_taxonomy_version": "test", "generated_at": "2026-01-01T00:00:00Z",
        },
        "product_type": "accommodation",
        "fields": fields,
    }
    extraction_response = await state.handlers["submit_extraction"]({"extraction": extraction})
    assert _payload(extraction_response)["status"] == "valid"
    duplicate_response = await state.handlers["submit_extraction"]({"extraction": extraction})
    assert _payload(duplicate_response)["status"] == "valid"
    assert state.extraction_submissions == 1
    assert calls.count("validate_extraction.py") == 1
    finalized = await state.handlers["finalize_outputs"]({"review_report": "# Review\n\nEvidence-grounded preparation completed."})
    final_payload = _payload(finalized)
    assert final_payload["status"] == "ok"
    assert set(final_payload["artifact_hashes"]) == {
        "result.json", "canonical-product.json", "result.xlsx", "review-report.md",
    }
    assert state.finalized is True
    assert calls == [
        "validate_source_manifest_optimized.py", "fetch_pages_optimized.py", "validate_extraction.py",
        "build_canonical_record.py", "export_xlsx.py",
    ]


