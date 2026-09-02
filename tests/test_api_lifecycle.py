import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import app.api as api_module


@pytest.fixture
def lifecycle_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "WORKSPACE_BASE", tmp_path / "runs")
    monkeypatch.setattr(
        api_module,
        "load_foundry_env",
        lambda *args, **kwargs: {"env": {}, "model": "test-model"},
    )
    with TestClient(api_module.app) as client:
        yield client, tmp_path / "runs"


def test_orphaned_workspace_is_reported_as_interrupted(lifecycle_client):
    client, runs_dir = lifecycle_client
    workspace = runs_dir / "orphaned-run"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(json.dumps({
        "website_urls": ["https://example.fi"],
    }), encoding="utf-8")

    (workspace / "work").mkdir()
    (workspace / "work" / "run-progress.json").write_text(json.dumps({
        "stage_reached": "stage_3",
    }), encoding="utf-8")

    response = client.get("/runs/orphaned-run")
    assert response.status_code == 200
    assert response.json()["status"] == "interrupted"
    assert response.json()["error_code"] == "backend_restarted"
    assert response.json()["stage_reached"] == "stage_3"


def test_library_does_not_describe_orphan_as_running(lifecycle_client):
    client, runs_dir = lifecycle_client
    workspace = runs_dir / "orphaned-run"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(json.dumps({
        "website_urls": ["https://example.fi"],
    }), encoding="utf-8")

    entry = client.get("/runs").json()["runs"][0]
    assert entry["status"] == "interrupted"
    assert entry["error_code"] == "backend_restarted"


def test_startup_reconciliation_persists_interrupted_manifest(lifecycle_client):
    _client, runs_dir = lifecycle_client
    workspace = runs_dir / "restart-run"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(
        json.dumps({"website_urls": ["https://example.fi"]}), encoding="utf-8",
    )
    (workspace / "work").mkdir()
    (workspace / "work" / "run-progress.json").write_text(
        json.dumps({"stage_reached": "stage_3"}), encoding="utf-8",
    )

    api_module._reconcile_orphaned_workspaces()

    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "interrupted"
    assert manifest["error_code"] == "backend_restarted"
    assert manifest["stage_reached"] == "stage_3"

@pytest.mark.asyncio
async def test_run_limited_reports_queued_until_semaphore_is_acquired(tmp_path, monkeypatch):
    semaphore = asyncio.Semaphore(1)
    await semaphore.acquire()
    monkeypatch.setattr(api_module, "_RUN_SEMAPHORE", semaphore)

    workspace = tmp_path / "queued-run"
    workspace.mkdir()
    api_module._RUN_PHASES[workspace.name] = "queued"
    called = asyncio.Event()

    async def fake_run_analysis(*args, **kwargs):
        called.set()
        return None

    monkeypatch.setattr(api_module, "run_analysis", fake_run_analysis)
    task = asyncio.create_task(api_module._run_limited(workspace, lambda event: None))
    await asyncio.sleep(0)

    assert api_module._RUN_PHASES[workspace.name] == "queued"
    assert not called.is_set()

    semaphore.release()
    await task
    assert called.is_set()
    assert api_module._RUN_PHASES[workspace.name] == "running"


@pytest.mark.asyncio
async def test_cancelling_queued_run_persists_terminal_manifest(tmp_path, monkeypatch):
    semaphore = asyncio.Semaphore(1)
    await semaphore.acquire()
    monkeypatch.setattr(api_module, "_RUN_SEMAPHORE", semaphore)
    workspace = tmp_path / "cancelled-run"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(
        json.dumps({"website_urls": ["https://example.fi"]}), encoding="utf-8",
    )
    api_module._RUN_PHASES[workspace.name] = "queued"

    task = asyncio.create_task(api_module._run_limited(workspace, lambda _event: None))
    await asyncio.sleep(0)
    task.cancel()
    outcome = await task

    assert outcome == {"status": "cancelled", "error_code": "run_cancelled"}
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "cancelled"


def test_sse_replays_persisted_terminal_history(lifecycle_client):
    client, runs_dir = lifecycle_client
    workspace = runs_dir / "persisted-events-run"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(
        json.dumps({"website_urls": ["https://example.fi"]}), encoding="utf-8",
    )
    (workspace / "work").mkdir()
    api_module.persist_stage_event(workspace, {"type": "stage", "stage": "stage_3"})
    api_module._persist_terminal_lifecycle(workspace, "interrupted", "backend_restarted")

    response = client.get("/runs/persisted-events-run/events")

    assert response.status_code == 200
    assert '"type": "stage"' in response.text
    assert '"type": "done"' in response.text
    assert '"status": "interrupted"' in response.text


def test_cancel_endpoint_persists_terminal_status_without_live_task(lifecycle_client):
    client, runs_dir = lifecycle_client
    workspace = runs_dir / "cancel-via-api"
    (workspace / "input").mkdir(parents=True)
    (workspace / "input" / "request.json").write_text(
        json.dumps({"website_urls": ["https://example.fi"]}), encoding="utf-8",
    )

    response = client.post("/runs/cancel-via-api/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    detail = client.get("/runs/cancel-via-api").json()
    assert detail["status"] == "cancelled"
    assert detail["error_code"] == "run_cancelled"


