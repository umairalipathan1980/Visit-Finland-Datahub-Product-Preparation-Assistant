"""One-session Claude Agent SDK runner using only coarse typed tools."""
from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from app.agent_tools import build_optimized_tool_server
from app.finalize import classify_and_finalize
from app.progress import persist_stage_event
from app.telemetry import RunTelemetry

WALL_CLOCK_TIMEOUT_S = 600
OPTIMIZED_TURN_CAP = 96
RECOVERY_TURN_CAP = 8


async def run_optimized_analysis(
    workspace: Path,
    package_dir: Path,
    env_bundle: dict,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    def emit(event: dict) -> None:
        persist_stage_event(workspace, event)
        if on_event is not None:
            on_event(event)

    telemetry = RunTelemetry("coarse_tools", emit)
    server, state, allowed_tools = build_optimized_tool_server(
        workspace, package_dir, telemetry,
    )

    def has_terminal_state() -> bool:
        if state.finalized or state.forced_status is not None:
            return True
        if state.extraction_submissions < 2:
            return False
        try:
            result = json.loads(
                (workspace / "work" / "staging-output" / "result.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return False
        return result.get("validation", {}).get("valid") is False

    stop_blocks = 0

    async def prevent_incomplete_stop(_input, _tool_use_id, _context):
        nonlocal stop_blocks
        if has_terminal_state() or stop_blocks >= 2:
            return {}
        stop_blocks += 1
        return {
            "decision": "block",
            "reason": (
                "The Visit Finland workflow is incomplete. Continue with the typed visit_finland tools. "
                "Do not repeat load_skill or prepare_sources and do not call Read, Bash, or generic tools. "
                "After source preparation, read every context page in cursor order. Then select returned "
                "candidate IDs with fetch_selected_pages or call record_scope when no additional page is needed. "
                "After every fetch, read all newly queued context pages. Continue through submit_extraction and "
                "finalize_outputs unless a typed tool reports a terminal outcome."
            ),
        }

    options = ClaudeAgentOptions(
        cwd=str(package_dir),
        env=env_bundle["env"],
        model=env_bundle["model"],
        tools=[],
        allowed_tools=allowed_tools,
        disallowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"],
        mcp_servers={"visit_finland": server},
        hooks={"Stop": [HookMatcher(hooks=[prevent_incomplete_stop])]},
        strict_mcp_config=True,
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=OPTIMIZED_TURN_CAP,
        include_partial_messages=True,
    )
    prompt = f"""Run the Visit Finland Accommodation preparation workflow for run {workspace.name}.

You have one continuous session and only seven task-specific tools. You have no shell or filesystem tools.
Call load_skill first and follow the returned SKILL.md completely, specifically its Optimized coarse-tool workflow.
Then call prepare_sources and follow its context cursor. Call read_context_page repeatedly, using exactly the
returned next cursor, until context_complete is true. Only then may you select relevant candidate link IDs and
call fetch_selected_pages once; use its one optional recovery call only when an unusual site structure justifies
it. After each fetch, read every newly queued context page before making another decision. Call prepare_sources
exactly once. Never call Read or any generic filesystem tool. Follow each tool's next_action instead.
Determine and record product scope. Whether scope is resolved or ambiguous, submit a complete extraction. For
ambiguous scope, never merge candidate products; mark scope-dependent fields review or missing and preserve the
alternatives and reasoning. Repair the extraction at most once when the deterministic validator permits repair,
then call finalize_outputs with your curator-facing review report, including any unresolved scope uncertainty.
If a tool reports a terminal outcome, stop. Never invent link IDs, source IDs, facts, or citations.
"""

    transcript: list = []
    forced_status: str | None = None
    forced_error_code: str | None = None
    result_turns: int | None = None
    result_session_id: str | None = None

    async def drain(query_prompt: str, query_options: ClaudeAgentOptions) -> None:
        nonlocal forced_status, forced_error_code, result_turns, result_session_id
        async for message in query(prompt=query_prompt, options=query_options):
            transcript.append(message)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        emit({"type": "reasoning", "text": block.text})
                    elif isinstance(block, ToolUseBlock):
                        telemetry.record_tool_call()
                        short_name = block.name.rsplit("__", 1)[-1]
                        if short_name == "record_scope":
                            state.stage_reached = "stage_4"
                            emit({
                                "type": "stage",
                                "stage": "stage_4",
                                "operation": "determine_scope",
                                "state": "started",
                            })
                        detail = ""
                        if short_name == "fetch_selected_pages":
                            detail = f"{len(block.input.get('link_ids', []))} selected links"
                        elif short_name == "submit_extraction":
                            detail = f"submission {state.extraction_submissions + 1}"
                        emit({"type": "tool_use", "tool": short_name, **({"detail": detail} if detail else {})})
                        print(f"[tool_use] {short_name}", file=sys.stderr)
            elif isinstance(message, UserMessage) and isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, ToolResultBlock) and block.is_error:
                        telemetry.model["tool_errors"] += 1
                        print(f"[tool_error] {str(block.content)[:200]}", file=sys.stderr)
            elif isinstance(message, ResultMessage):
                result_turns = (result_turns or 0) + message.num_turns
                result_session_id = message.session_id
                print(
                    f"[result] subtype={message.subtype} is_error={message.is_error} "
                    f"num_turns={message.num_turns} stop_reason={message.stop_reason}",
                    file=sys.stderr,
                )
                if not state.finalized:
                    if message.subtype == "error_max_turns":
                        forced_status, forced_error_code = "execution_failed", "turn_limit_exceeded"
                    elif message.is_error:
                        forced_status, forced_error_code = "execution_failed", "model_error"

    started_at = asyncio.get_running_loop().time()
    try:
        await asyncio.wait_for(drain(prompt, options), timeout=WALL_CLOCK_TIMEOUT_S)
        remaining_turns = OPTIMIZED_TURN_CAP - (result_turns or 0)
        if (
            forced_status is None
            and state.skill_loaded
            and not has_terminal_state()
            and result_session_id
            and remaining_turns > 0
        ):
            recovery_prompt = f"""The workflow stopped before reaching a terminal outcome.

Continue the same run from its current deterministic state:
- prepared: {state.prepared}
- expansion calls used: {state.expansion_calls}
- unread context pages: {len(getattr(state, 'pending_context_cursors', []))}
- scope status: {state.scope_status}
- extraction submissions: {state.extraction_submissions}

Do not call load_skill or prepare_sources again. Do not call Read, Bash, or any generic tool.
Use only the seven visit_finland tools already available and follow their next_action fields.
If context pages remain, call read_context_page with the returned cursor until complete. If candidate link IDs
were returned, select relevant IDs and call fetch_selected_pages; otherwise call record_scope.
Continue through extraction, validation, and finalize_outputs unless a typed tool reports a terminal outcome.
"""
            recovery_options = replace(
                options,
                resume=result_session_id,
                max_turns=min(RECOVERY_TURN_CAP, remaining_turns),
            )
            remaining_seconds = max(
                1.0,
                WALL_CLOCK_TIMEOUT_S - (asyncio.get_running_loop().time() - started_at),
            )
            await asyncio.wait_for(
                drain(recovery_prompt, recovery_options),
                timeout=remaining_seconds,
            )
        if forced_status is None and state.skill_loaded and not has_terminal_state():
            forced_status, forced_error_code = "execution_failed", "workflow_incomplete"
    except asyncio.TimeoutError:
        forced_status, forced_error_code = "execution_failed", "agent_timeout"
    except asyncio.CancelledError:
        forced_status, forced_error_code = "cancelled", "run_cancelled"
    except Exception as exc:
        print(f"[runner_error] {type(exc).__name__}: {exc}", file=sys.stderr)
        forced_status, forced_error_code = "execution_failed", "internal_error"

    if state.forced_status is not None:
        forced_status, forced_error_code = state.forced_status, state.forced_error_code
    if not state.skill_loaded and forced_status is None:
        forced_status, forced_error_code = "execution_failed", "skill_load_failed"

    telemetry.record_model_result(turns=result_turns, transcript_messages=len(transcript))
    telemetry_snapshot = telemetry.snapshot()
    outcome = classify_and_finalize(
        workspace,
        denials=[],
        verification_method="typed_load_skill" if state.skill_loaded else None,
        forced_status=forced_status,
        forced_error_code=forced_error_code,
        stage_reached=state.stage_reached,
    )
    telemetry_snapshot["terminal_status"] = outcome["status"]
    telemetry_snapshot["terminal_error_code"] = outcome.get("error_code")
    telemetry_snapshot["evidence_chars_returned"] = state.evidence_chars_returned
    telemetry_snapshot["context_chars_queued"] = getattr(state, "context_chars_queued", 0)
    telemetry_snapshot["context_pages_queued"] = len(getattr(state, "context_pages", {}))
    telemetry_snapshot["context_pages_delivered"] = len(getattr(state, "delivered_context_cursors", set()))
    manifest_path = workspace / "output" / "run-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["telemetry"] = telemetry_snapshot
        if state.artifact_hashes:
            manifest["artifact_hashes"] = state.artifact_hashes
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    outcome["transcript_length"] = len(transcript)
    emit({"type": "done", **outcome})
    return outcome



