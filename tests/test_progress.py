import json

from app.progress import EVENT_HISTORY_LIMIT, load_persisted_events, persist_stage_event


def test_stage_progress_is_written_atomically(workspace):
    persist_stage_event(workspace, {
        "type": "stage",
        "stage": "stage_3",
        "operation": "fetch_seed_pages",
        "state": "completed",
        "duration_ms": 42,
    })

    progress = json.loads((workspace / "work" / "run-progress.json").read_text(encoding="utf-8"))
    assert progress["stage_reached"] == "stage_3"
    assert progress["operation"] == "fetch_seed_pages"
    assert progress["state"] == "completed"
    assert progress["duration_ms"] == 42


def test_non_stage_event_does_not_create_progress_file(workspace):
    persist_stage_event(workspace, {"type": "done", "status": "completed"})
    assert not (workspace / "work" / "run-progress.json").exists()


def test_operational_events_are_durable_and_bounded(workspace):
    persist_stage_event(workspace, {"type": "reasoning", "text": "not persisted"})
    for index in range(EVENT_HISTORY_LIMIT + 2):
        persist_stage_event(workspace, {"type": "tool_use", "tool": f"tool-{index}"})
    persist_stage_event(workspace, {"type": "done", "status": "completed", "error_code": None})

    events = load_persisted_events(workspace)
    assert len(events) == EVENT_HISTORY_LIMIT
    assert all(event["type"] != "reasoning" for event in events)
    assert events[-1]["type"] == "done"


