import asyncio
import json

import pytest

import app.agent_tools as agent_tools
from app.agent_tools import ALLOWED_TOOL_NAMES, build_optimized_tool_server
from app.telemetry import RunTelemetry
from conftest import PACKAGE_DIR


def build_tools(workspace):
    telemetry = RunTelemetry("test")
    server, state, allowed = build_optimized_tool_server(workspace, PACKAGE_DIR, telemetry)
    return server, state, allowed, telemetry


def test_scope_tool_schema_exposes_valid_statuses_and_error_codes():
    schema_text = json.dumps(agent_tools.ScopeInput.model_json_schema())

    assert '"resolved"' in schema_text
    assert '"scope_ambiguous"' in schema_text
    assert '"multiple_accommodation_products"' in schema_text
    assert '"product_boundary_unclear"' in schema_text


@pytest.mark.asyncio
async def test_load_skill_is_narrow_and_returns_verified_policy(workspace):
    _server, state, allowed, telemetry = build_tools(workspace)
    assert allowed == ALLOWED_TOOL_NAMES
    assert all(name.startswith("mcp__visit_finland__") for name in allowed)
    assert not any(name.endswith(("Bash", "Read", "Write", "Edit")) for name in allowed)

    response = await state.handlers["load_skill"]({})
    payload = json.loads(response["content"][0]["text"])
    assert response["is_error"] is False
    assert payload["status"] == "ok"
    assert len(payload["skill_sha256"]) == 64
    assert "Optimized coarse-tool workflow" in payload["skill"]
    assert payload["schemas"]["extraction"]["$id"] == "accommodation-extraction.schema.json"
    assert state.skill_loaded is True
    assert telemetry.operations[0]["name"] == "load_skill"
    assert telemetry.operations[0]["retry_count"] == 0


@pytest.mark.asyncio
async def test_prepare_requires_skill_load(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    response = await state.handlers["prepare_sources"]({})
    assert response["is_error"] is True
    assert "skill_not_loaded" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_tool_inputs_reject_unknown_properties(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    response = await state.handlers["load_skill"]({"path": "another-file.md"})
    assert response["is_error"] is True
    assert "invalid_tool_input" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_link_ids_cannot_be_forged(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.prepared = True
    (workspace / "work" / "link-candidates.json").write_text('{"links": []}', encoding="utf-8")
    response = await state.handlers["fetch_selected_pages"]({"link_ids": ["l999"], "reason": "test"})
    assert response["is_error"] is True
    assert "unknown_link_ids" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_resolved_scope_rejects_unknown_source_ids(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.prepared = True
    response = await state.handlers["record_scope"]({"scope_decision": {
        "status": "resolved",
        "error_code": None,
        "product": {"pages": ["p999"], "summary": "one product"},
        "excluded": [],
        "additional_products": [],
        "out_of_type_facilities": [],
    }})
    assert response["is_error"] is True
    assert "unknown_scope_sources" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_scope_tool_rejects_unknown_status_at_input_boundary(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.prepared = True

    response = await state.handlers["record_scope"]({"scope_decision": {
        "status": "single_product",
        "error_code": None,
        "product": {"pages": ["p001"], "summary": "one product"},
        "excluded": [],
        "additional_products": [],
        "out_of_type_facilities": [],
    }})

    assert response["is_error"] is True
    assert "invalid_tool_input" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_ambiguous_scope_continues_to_extraction_with_review_instruction(workspace, monkeypatch):
    async def invalid_validation(state, script_name, *args):
        assert script_name == "validate_extraction.py"
        output = workspace / "work" / "staging-output" / "result.json"
        agent_tools._write_json_atomic(output, {
            "fields": {},
            "validation": {"valid": False, "errors": [{"rule_id": "schema_violation"}], "warnings": []},
        })
        return {"returncode": 4, "result": {"status": "invalid"}, "error": None}

    monkeypatch.setattr(agent_tools, "_run_script", invalid_validation)
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.prepared = True

    response = await state.handlers["record_scope"]({"scope_decision": {
        "status": "scope_ambiguous",
        "error_code": "product_boundary_unclear",
        "reason": "The page names two properties without a reliable product boundary.",
        "product": None,
        "excluded": [],
        "additional_products": [],
        "out_of_type_facilities": [],
    }})
    payload = json.loads(response["content"][0]["text"])

    assert response["is_error"] is False
    assert payload["continue_to_extraction"] is True
    assert payload["review_required"] is True
    extraction = await state.handlers["submit_extraction"]({"extraction": {}})
    assert "scope_not_resolved" not in extraction["content"][0]["text"]
    assert json.loads(extraction["content"][0]["text"])["status"] == "invalid"


@pytest.mark.asyncio
async def test_extraction_and_finalization_are_ordered(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    extraction = await state.handlers["submit_extraction"]({"extraction": {}})
    finalization = await state.handlers["finalize_outputs"]({"review_report": "# Review\nNot valid yet."})
    assert extraction["is_error"] is True
    assert "scope_not_resolved" in extraction["content"][0]["text"]
    assert finalization["is_error"] is True
    assert "extraction_not_valid" in finalization["content"][0]["text"]


@pytest.mark.asyncio
async def test_no_usable_sources_is_terminal_before_scope(workspace):
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.prepared = True
    state.forced_status = "no_usable_sources"
    state.forced_error_code = "all_pages_inaccessible"
    response = await state.handlers["record_scope"]({"scope_decision": {
        "status": "resolved",
        "product": {"pages": [], "summary": "should not be accepted"},
        "excluded": [],
        "additional_products": [],
        "out_of_type_facilities": [],
    }})
    payload = json.loads(response["content"][0]["text"])
    assert payload == {
        "status": "no_usable_sources",
        "error_code": "all_pages_inaccessible",
        "terminal": True,
    }
    assert not (workspace / "work" / "scope-decision.json").exists()


@pytest.mark.asyncio
async def test_exactly_one_distinct_repair_is_permitted(workspace, monkeypatch):
    calls = 0

    async def invalid_validation(state, script_name, *args):
        nonlocal calls
        assert script_name == "validate_extraction.py"
        calls += 1
        result_path = workspace / "work" / "staging-output" / "result.json"
        agent_tools._write_json_atomic(result_path, {
            "fields": {},
            "validation": {
                "valid": False,
                "errors": [{"rule_id": "schema_violation"}],
                "warnings": [],
            },
        })
        return {"returncode": 4, "result": {"status": "invalid"}, "error": None}

    monkeypatch.setattr(agent_tools, "_run_script", invalid_validation)
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.scope_status = "resolved"

    first = await state.handlers["submit_extraction"]({"extraction": {"attempt": 1}})
    duplicate = await state.handlers["submit_extraction"]({"extraction": {"attempt": 1}})
    repair = await state.handlers["submit_extraction"]({"extraction": {"attempt": 2}})
    third = await state.handlers["submit_extraction"]({"extraction": {"attempt": 3}})

    assert json.loads(first["content"][0]["text"])["repair_allowed"] is True
    assert duplicate == first
    assert json.loads(repair["content"][0]["text"])["repair_allowed"] is False
    assert "repair_limit_reached" in third["content"][0]["text"]
    assert calls == 2


@pytest.mark.asyncio
async def test_concurrent_duplicate_tool_calls_cannot_overlap(workspace, monkeypatch):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def slow_validation(state, script_name, *args):
        entered.set()
        await release.wait()
        agent_tools._write_json_atomic(
            workspace / "work" / "staging-output" / "result.json",
            {"fields": {}, "validation": {"valid": False, "errors": [], "warnings": []}},
        )
        return {"returncode": 4, "result": {"status": "invalid"}, "error": None}

    monkeypatch.setattr(agent_tools, "_run_script", slow_validation)
    _server, state, _allowed, _telemetry = build_tools(workspace)
    state.scope_status = "resolved"
    args = {"extraction": {"attempt": 1}}
    first_task = asyncio.create_task(state.handlers["submit_extraction"](args))
    await entered.wait()

    overlapping = await state.handlers["submit_extraction"](args)
    release.set()
    await first_task

    assert overlapping["is_error"] is True
    assert "operation_in_progress" in overlapping["content"][0]["text"]
    assert state.extraction_submissions == 1
