"""Foundry environment loading and resolution (plan Section 2 / Section 9)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

REQUIRED_VARS = ["CLAUDE_CODE_USE_FOUNDRY", "ANTHROPIC_FOUNDRY_API_KEY", "ANTHROPIC_FOUNDRY_RESOURCE"]
DEFAULT_MODEL = "claude-sonnet-5"


class EnvironmentError_(RuntimeError):
    pass


def load_foundry_env(
    env_file: Path | None,
    model_override: str | None,
    allow_nested: bool = True,
) -> dict:
    file_values = dotenv_values(str(env_file)) if env_file and env_file.is_file() else {}
    merged = {**file_values, **os.environ}  # process environment wins over the file, per plan Section 2

    missing = [name for name in REQUIRED_VARS if not merged.get(name)]
    if missing:
        raise EnvironmentError_(f"Missing required environment variable(s): {', '.join(missing)}")

    if merged.get("CLAUDECODE") and not allow_nested:
        raise EnvironmentError_(
            "Refusing to start inside an existing Claude Code session (CLAUDECODE is set). "
            "Enable nested-session support to run from an existing Claude Code session."
        )

    resolved_env = dict(merged)
    if allow_nested:
        resolved_env.pop("CLAUDECODE", None)
        resolved_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    resolved_env.setdefault("API_TIMEOUT_MS", "600000")
    resolved_env.setdefault("CLAUDE_CODE_MAX_RETRIES", "2")
    resolved_env.setdefault("DISABLE_TELEMETRY", "1")

    model = (
        model_override
        or resolved_env.get("ANTHROPIC_MODEL")
        or resolved_env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        or DEFAULT_MODEL
    )

    return {"env": resolved_env, "model": model}


def redact(env: dict) -> dict:
    return {k: ("<redacted>" if "KEY" in k or "SECRET" in k or "TOKEN" in k else v) for k, v in env.items()}
