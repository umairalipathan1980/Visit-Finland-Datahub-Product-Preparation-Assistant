import asyncio
import json
from types import SimpleNamespace

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock

import app.runner as runner
import app.runner_optimized as optimized


@pytest.mark.asyncio
async def test_optimized_runner_exposes_only_typed_tools(workspace, monkeypatch):
    captured = {}

    async def fake_query(*, prompt, options):
        captured["prompt"] = prompt
        captured["options"] = options
        if False:
            yield None

    monkeypatch.setattr(optimized, "query", fake_query)
    outcome = await optimized.run_optimized_analysis(
        workspace,
        optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation",
        {"env": {}, "model": "test-model"},
    )

    options = captured["options"]
    assert options.tools == []
    assert "Bash" in options.disallowed_tools
    assert all(name.startswith("mcp__visit_finland__") for name in options.allowed_tools)
    assert set(options.mcp_servers) == {"visit_finland"}
    assert set(options.hooks) == {"Stop"}
    assert options.max_turns == optimized.OPTIMIZED_TURN_CAP
    assert outcome["status"] == "execution_failed"
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["error_code"] == "skill_load_failed"
    assert manifest["telemetry"]["workflow_mode"] == "coarse_tools"


@pytest.mark.asyncio
async def test_stop_hook_blocks_an_incomplete_workflow(workspace, monkeypatch):
    captured = {}

    async def fake_query(*, prompt, options):
        hook = options.hooks["Stop"][0].hooks[0]
        captured["first"] = await hook({"stop_hook_active": False}, None, {})
        captured["second"] = await hook({"stop_hook_active": True}, None, {})
        captured["third"] = await hook({"stop_hook_active": True}, None, {})
        if False:
            yield None

    monkeypatch.setattr(optimized, "query", fake_query)
    await optimized.run_optimized_analysis(
        workspace,
        optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation",
        {"env": {}, "model": "test-model"},
    )

    assert captured["first"]["decision"] == "block"
    assert "fetch_selected_pages" in captured["first"]["reason"]
    assert captured["second"]["decision"] == "block"
    assert captured["third"] == {}


@pytest.mark.asyncio
async def test_optimized_runner_cancellation_is_terminal(workspace, monkeypatch):
    async def cancelled_query(*, prompt, options):
        raise asyncio.CancelledError
        yield

    monkeypatch.setattr(optimized, "query", cancelled_query)
    outcome = await optimized.run_optimized_analysis(
        workspace,
        optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation",
        {"env": {}, "model": "test-model"},
    )

    assert outcome == {
        "status": "cancelled",
        "error_code": "run_cancelled",
        "transcript_length": 0,
    }
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "cancelled"
    assert manifest["telemetry"]["terminal_status"] == "cancelled"


@pytest.mark.asyncio
async def test_application_runner_always_uses_optimized_workflow(workspace, monkeypatch):
    called = {}

    async def fake_optimized(workspace_arg, package_arg, env_arg, on_event=None):
        called["values"] = (workspace_arg, package_arg, env_arg, on_event)
        return {"status": "completed", "error_code": None}

    monkeypatch.setattr(runner, "run_optimized_analysis", fake_optimized)
    package_dir = optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation"
    env = {"env": {}, "model": "test-model"}

    outcome = await runner.run_analysis(workspace, package_dir, env)

    assert outcome["status"] == "completed"
    assert called["values"][:3] == (workspace, package_dir, env)


@pytest.mark.asyncio
async def test_scope_tool_attempt_advances_progress_before_validation(workspace, monkeypatch):
    events = []

    async def fake_query(*, prompt, options):
        yield AssistantMessage(
            content=[ToolUseBlock(
                id="scope-call",
                name="mcp__visit_finland__record_scope",
                input={"scope_decision": {"status": "invalid"}},
            )],
            model="test-model",
        )

    monkeypatch.setattr(optimized, "query", fake_query)
    await optimized.run_optimized_analysis(
        workspace,
        optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation",
        {"env": {}, "model": "test-model"},
        on_event=events.append,
    )

    assert {
        "type": "stage",
        "stage": "stage_4",
        "operation": "determine_scope",
        "state": "started",
    } in events


@pytest.mark.asyncio
async def test_incomplete_success_resumes_same_session_once(workspace, monkeypatch):
    state = SimpleNamespace(
        finalized=False,
        forced_status=None,
        forced_error_code=None,
        skill_loaded=True,
        prepared=True,
        expansion_calls=0,
        scope_status=None,
        extraction_submissions=0,
        stage_reached="stage_3",
        evidence_chars_returned=100,
        artifact_hashes={},
    )
    monkeypatch.setattr(
        optimized,
        "build_optimized_tool_server",
        lambda *_args, **_kwargs: (object(), state, []),
    )
    calls = []

    async def fake_query(*, prompt, options):
        calls.append((prompt, options))
        yield ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=2,
            session_id="test-session",
            stop_reason="end_turn",
        )

    monkeypatch.setattr(optimized, "query", fake_query)
    outcome = await optimized.run_optimized_analysis(
        workspace,
        optimized.Path(__file__).resolve().parents[1] / "visit-finland-datahub-accommodation",
        {"env": {}, "model": "test-model"},
    )

    assert len(calls) == 2
    assert calls[1][1].resume == "test-session"
    assert "Do not call load_skill or prepare_sources again" in calls[1][0]
    assert outcome["status"] == "execution_failed"
    assert outcome["error_code"] == "workflow_incomplete"
