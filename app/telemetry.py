"""Operational run telemetry for both workflow modes."""
from __future__ import annotations

import datetime
import time
from dataclasses import dataclass, field
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@dataclass
class RunTelemetry:
    workflow_mode: str
    emit: Callable[[dict], None] = lambda _event: None
    started_at: str = field(default_factory=_now_iso)
    _started_monotonic: float = field(default_factory=time.monotonic)
    operations: list[dict[str, Any]] = field(default_factory=list)
    model: dict[str, Any] = field(default_factory=lambda: {
        "turns": None, "transcript_messages": 0, "tool_calls": 0, "tool_errors": 0,
    })

    def start_operation(self, name: str, stage: str | None = None, **counts: Any) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "name": name,
            "stage": stage,
            "started_at": _now_iso(),
            "_started_monotonic": time.monotonic(),
            "retry_count": 0,
            **counts,
        }
        self.operations.append(entry)
        if stage:
            self.emit({"type": "stage", "stage": stage, "operation": name, "state": "started"})
        return entry

    def finish_operation(self, entry: dict[str, Any], status: str = "ok", **counts: Any) -> None:
        started = entry.pop("_started_monotonic", time.monotonic())
        entry.update({
            "status": status,
            "finished_at": _now_iso(),
            "duration_ms": round((time.monotonic() - started) * 1000),
            **counts,
        })
        if entry.get("stage"):
            self.emit({
                "type": "stage", "stage": entry["stage"], "operation": entry["name"],
                "state": "completed" if status == "ok" else "failed",
                "duration_ms": entry["duration_ms"],
            })

    def record_tool_call(self, is_error: bool = False) -> None:
        self.model["tool_calls"] += 1
        if is_error:
            self.model["tool_errors"] += 1

    def record_model_result(self, *, turns: int | None, transcript_messages: int) -> None:
        self.model["turns"] = turns
        self.model["transcript_messages"] = transcript_messages

    def snapshot(self) -> dict[str, Any]:
        operations = []
        for raw in self.operations:
            entry = dict(raw)
            started = entry.pop("_started_monotonic", None)
            if started is not None and "duration_ms" not in entry:
                entry.update({
                    "status": "interrupted", "finished_at": _now_iso(),
                    "duration_ms": round((time.monotonic() - started) * 1000),
                })
            operations.append(entry)
        return {
            "workflow_mode": self.workflow_mode,
            "started_at": self.started_at,
            "finished_at": _now_iso(),
            "duration_ms": round((time.monotonic() - self._started_monotonic) * 1000),
            "operations": operations,
            "model": dict(self.model),
        }
