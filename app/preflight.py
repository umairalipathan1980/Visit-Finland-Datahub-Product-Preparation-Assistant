"""Foundry preflight (plan Section 10)."""
from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query


async def run_preflight(env_bundle: dict, package_dir: Path) -> dict:
    options = ClaudeAgentOptions(
        cwd=str(package_dir),
        env=env_bundle["env"],
        model=env_bundle["model"],
        allowed_tools=[],
        setting_sources=[],
        max_turns=1,
    )
    reply_text = ""
    try:
        async for message in query(prompt="Reply with the single word: READY", options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        reply_text += block.text
    except Exception as exc:
        return {"ready": False, "reason": f"{type(exc).__name__}: {exc}"}

    ready = "READY" in reply_text.upper()
    return {
        "ready": ready,
        "reply": reply_text.strip(),
        "model": env_bundle["model"],
        "capability_report": {
            "model": env_bundle["model"],
            "hosting": "azure",
            "web_search": {"available": None, "basis": "not_probed"},
            "web_fetch": {"available": None, "basis": "not_probed"},
            "api_skills": {"available": False, "basis": "hosting_documentation"},
        },
    }
