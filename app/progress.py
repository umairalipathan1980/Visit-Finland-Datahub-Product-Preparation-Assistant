"""Durable progress snapshots and replayable operational event history."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any


EVENT_HISTORY_LIMIT = 250
_DURABLE_EVENT_TYPES = {"stage", "tool_use", "skill_loaded", "done"}


def persist_stage_event(workspace: Path, event: dict[str, Any]) -> None:
    """Atomically retain the latest stage event for restart diagnostics.

    Terminal truth still belongs to output/run-manifest.json. The latest stage
    remains under work/, while bounded operational events live at the run root
    so successful workspace pruning does not remove reconnect history.
    """
    work_dir = workspace / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    if event.get("type") in _DURABLE_EVENT_TYPES:
        history_path = workspace / "run-events.json"
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except (OSError, json.JSONDecodeError):
            history = []
        durable_event = dict(event)
        durable_event.setdefault("recorded_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
        history = [*history, durable_event][-EVENT_HISTORY_LIMIT:]
        history_temp = history_path.with_name(f".{history_path.name}.tmp")
        history_temp.write_text(json.dumps(history, indent=2), encoding="utf-8")
        os.replace(history_temp, history_path)

    if event.get("type") == "stage":
        path = work_dir / "run-progress.json"
        payload = {
            "stage_reached": event.get("stage"),
            "operation": event.get("operation"),
            "state": event.get("state"),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if "duration_ms" in event:
            payload["duration_ms"] = event["duration_ms"]
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temporary, path)


def load_persisted_events(workspace: Path) -> list[dict[str, Any]]:
    path = workspace / "run-events.json"
    try:
        events = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return events if isinstance(events, list) else []
