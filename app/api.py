"""Thin HTTP service exposing the runner over the endpoint contract in plan
Section 15 ("Frontend integration surface").

A separate long-lived Python process from both the CLI entrypoint
(app/main.py) and any future Next.js frontend -- not Next.js route handlers.
Section 15 gives the three independent reasons: the wall-clock cap exceeds a
request-scoped function, the runner spawns the `claude` CLI as a subprocess,
and `bypassPermissions` must stay isolated to this worker rather than share
a process with the web tier.

Run with: uvicorn app.api:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import asyncio
import datetime
import json
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from app.env_loader import EnvironmentError_, load_foundry_env
from app.finalize import classify_and_finalize
from app.progress import load_persisted_events, persist_stage_event
from app.runner import run_analysis
from app.uploads import store_uploads
from app.workspace import build_request_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "visit-finland-datahub-accommodation"
WORKSPACE_BASE = REPO_ROOT / "runs"
DEFAULT_ENV_FILE = REPO_ROOT / ".env"

# The fixed enum from Section 15: an artifact is addressed by name, never by
# a client-supplied path, so a workspace path can never reach the browser.
ARTIFACT_NAMES = {
    "result.json", "canonical-product.json", "result.xlsx", "review-report.md",
    "run-manifest.json", "scope-decision.json", "extraction-draft.json", "sources.json",
    "approved-product.json",
}

# In-memory registry of in-flight runs. On startup, persisted nonterminal
# workspaces are reconciled to an interrupted terminal manifest.
_RUN_TASKS: dict[str, asyncio.Task] = {}
_RUN_PHASES: dict[str, str] = {}
_ENV_BUNDLE: dict = {}
DEFAULT_MAX_CONCURRENT_RUNS = 2
_RUN_SEMAPHORE = asyncio.Semaphore(DEFAULT_MAX_CONCURRENT_RUNS)

# Progress events per run. A bounded operational subset is also persisted for
# reconnect/restart replay; free-form reasoning remains memory-only.
_EVENT_HISTORY: dict[str, list[dict]] = {}
_EVENT_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}
EVENT_HISTORY_LIMIT = 250


def _read_json_or_none(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _product_name_from_record(record: dict | None) -> str | None:
    if not isinstance(record, dict):
        return None
    fields = record.get("fields")
    if not isinstance(fields, dict):
        return None
    name = fields.get("name")
    if isinstance(name, str):
        return name.strip() or None
    if not isinstance(name, dict):
        return None
    for locale in ("en", "fi"):
        value = name.get(locale)
        if isinstance(value, dict):
            value = value.get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _stage_reached(workspace: Path) -> str:
    progress = _read_json_or_none(workspace / "work" / "run-progress.json") or {}
    return progress.get("stage_reached") or "stage_0_bootstrap"


def _persist_terminal_lifecycle(workspace: Path, status: str, error_code: str) -> dict:
    manifest_path = workspace / "output" / "run-manifest.json"
    manifest = _read_json_or_none(manifest_path)
    if manifest is not None:
        return {"status": manifest["status"], "error_code": manifest.get("error_code")}
    outcome = classify_and_finalize(
        workspace,
        denials=[],
        verification_method=None,
        forced_status=status,
        forced_error_code=error_code,
        stage_reached=_stage_reached(workspace),
    )
    persist_stage_event(workspace, {"type": "done", **outcome})
    return outcome


def _reconcile_orphaned_workspaces() -> None:
    for workspace in WORKSPACE_BASE.iterdir():
        if (
            workspace.is_dir()
            and (workspace / "input" / "request.json").is_file()
            and not (workspace / "output" / "run-manifest.json").is_file()
        ):
            _persist_terminal_lifecycle(workspace, "interrupted", "backend_restarted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _RUN_SEMAPHORE
    try:
        _ENV_BUNDLE.update(load_foundry_env(DEFAULT_ENV_FILE, None))
    except EnvironmentError_ as exc:
        raise RuntimeError(f"API startup failed: {exc}") from exc
    try:
        concurrency = int(_ENV_BUNDLE.get("env", {}).get("MAX_CONCURRENT_RUNS", DEFAULT_MAX_CONCURRENT_RUNS))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("API startup failed: MAX_CONCURRENT_RUNS must be an integer") from exc
    _RUN_SEMAPHORE = asyncio.Semaphore(max(1, concurrency))
    WORKSPACE_BASE.mkdir(parents=True, exist_ok=True)
    _reconcile_orphaned_workspaces()
    try:
        yield
    finally:
        active = [(run_id, task) for run_id, task in _RUN_TASKS.items() if not task.done()]
        for run_id, task in active:
            _RUN_PHASES[run_id] = "cancelled"
            task.cancel()
        if active:
            await asyncio.gather(*(task for _run_id, task in active), return_exceptions=True)
        for run_id, _task in active:
            workspace = WORKSPACE_BASE / run_id
            if workspace.is_dir():
                _persist_terminal_lifecycle(workspace, "cancelled", "shutdown_cancelled")


app = FastAPI(title="Visit Finland DataHub product preparation API", lifespan=lifespan)

# Dev-only: the Next.js frontend runs on a different origin (localhost:3000)
# than this API (localhost:8010). Restricted to localhost dev ports, not "*",
# since bypassPermissions-adjacent state (run artifacts) is reachable through
# this API and shouldn't be readable by an arbitrary origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Unauthenticated liveness/readiness probe target for container platforms."""
    return {"status": "ok"}


def _workspace_for(run_id: str) -> Path:
    # run_id is used only to join a path under WORKSPACE_BASE and is checked
    # for traversal before that join -- see the resolve()/relative_to() guard
    # in each handler below, not here, so every caller gets the same check.
    workspace = WORKSPACE_BASE / run_id
    resolved = workspace.resolve()
    try:
        resolved.relative_to(WORKSPACE_BASE.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="unknown run_id")
    if not resolved.is_dir():
        raise HTTPException(status_code=404, detail="unknown run_id")
    return resolved


async def _run_limited(workspace: Path, on_event):
    try:
        async with _RUN_SEMAPHORE:
            _RUN_PHASES[workspace.name] = "running"
            return await run_analysis(workspace, PACKAGE_DIR, _ENV_BUNDLE, on_event=on_event)
    except asyncio.CancelledError:
        outcome = _persist_terminal_lifecycle(workspace, "cancelled", "run_cancelled")
        on_event({"type": "done", **outcome})
        return outcome


@app.post("/runs", status_code=202)
async def create_run(
    website_urls: list[str] = Form(...),
    product_type: str = Form("accommodation"),
    documents: list[UploadFile] = File(default=[]),
):
    website_urls = [u for u in website_urls if u.strip()]
    if not website_urls:
        raise HTTPException(status_code=400, detail="at least one website_urls entry is required")
    if product_type not in {"accommodation", "shops"}:
        raise HTTPException(status_code=400, detail="product_type must be accommodation or shops")

    tmp_dir = Path(tempfile.mkdtemp(prefix="upload-", dir=WORKSPACE_BASE))
    try:
        tmp_doc_paths = await store_uploads(documents, tmp_dir)

        workspace = build_request_workspace(
            WORKSPACE_BASE, website_urls, tmp_doc_paths, product_type=product_type,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    run_id = workspace.name
    _RUN_PHASES[run_id] = "queued"
    _EVENT_HISTORY[run_id] = []
    _EVENT_SUBSCRIBERS[run_id] = []

    def on_event(event: dict) -> None:
        history = _EVENT_HISTORY[run_id]
        history.append(event)
        if len(history) > EVENT_HISTORY_LIMIT:
            del history[:-EVENT_HISTORY_LIMIT]
        for queue in _EVENT_SUBSCRIBERS.get(run_id, []):
            queue.put_nowait(event)

    task = asyncio.create_task(_run_limited(workspace, on_event))
    _RUN_TASKS[run_id] = task
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    workspace = _workspace_for(run_id)
    request = _read_json_or_none(workspace / "input" / "request.json") or {}
    product_type = request.get("product_type", "accommodation")
    manifest_path = workspace / "output" / "run-manifest.json"

    if not manifest_path.is_file():
        progress = _read_json_or_none(workspace / "work" / "run-progress.json") or {}
        # artifacts/error_code/stage_reached are always present in the
        # response, even before a manifest exists, so a caller never has to
        # special-case "running" vs. a terminal status by key presence.
        task = _RUN_TASKS.get(run_id)
        if task is None:
            # No in-memory task (e.g. the API process restarted) and no
            # manifest yet -- honestly "unknown" rather than a guessed status.
            return {"run_id": run_id, "product_type": product_type, "status": "interrupted", "error_code": "backend_restarted",
                     "stage_reached": progress.get("stage_reached"), "artifacts": []}
        if task.done() and task.exception() is not None:
            # run_analysis's own try/except should already have written a
            # manifest for every failure; a bare exception escaping it is a
            # bug in the runner, not a normal terminal outcome. Surface it
            # rather than silently reporting "running" forever.
            raise HTTPException(status_code=500, detail=f"run task raised: {task.exception()!r}")
        return {"run_id": run_id, "product_type": product_type, "status": _RUN_PHASES.get(run_id, "running"), "error_code": None,
                 "stage_reached": progress.get("stage_reached"), "artifacts": []}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = workspace / "output"
    available = sorted(p.name for p in output_dir.iterdir() if p.is_file())
    return {
        "run_id": run_id,
        "product_type": product_type,
        "status": manifest["status"],
        "error_code": manifest.get("error_code"),
        "stage_reached": manifest.get("stage_reached"),
        "artifacts": available,
    }


@app.get("/runs")
async def list_runs():
    """The library: one entry per workspace directory, newest first. No
    separate index is kept -- request.json and run-manifest.json already
    carry everything a list view needs, and scanning stays correct even if
    the API process restarts (Section 15's known gap: no run index)."""
    if not WORKSPACE_BASE.is_dir():
        return {"runs": []}

    entries = []
    for entry_dir in WORKSPACE_BASE.iterdir():
        if not entry_dir.is_dir() or not (entry_dir / "input" / "request.json").is_file():
            continue  # skip stray temp-upload dirs and anything not a real run workspace
        request = _read_json_or_none(entry_dir / "input" / "request.json") or {}
        output_dir = entry_dir / "output"
        manifest = _read_json_or_none(output_dir / "run-manifest.json")
        product_name = (
            _product_name_from_record(_read_json_or_none(output_dir / "approved-product.json"))
            or _product_name_from_record(_read_json_or_none(output_dir / "canonical-product.json"))
            or _product_name_from_record(_read_json_or_none(output_dir / "result.json"))
        )
        run_id = entry_dir.name
        if manifest is not None:
            status = manifest["status"]
            error_code = manifest.get("error_code")
            approved = manifest.get("approved", False)
        else:
            is_live = run_id in _RUN_TASKS and not _RUN_TASKS[run_id].done()
            status = _RUN_PHASES.get(run_id, "running") if is_live else "interrupted"
            error_code = None if is_live else "backend_restarted"
            approved = False
        entries.append({
            "run_id": run_id,
            "product_type": request.get("product_type", "accommodation"),
            "product_name": product_name,
            "website_urls": request.get("website_urls", []),
            "status": status,
            "error_code": error_code,
            "approved": approved,
            "created_at": datetime.datetime.fromtimestamp(
                entry_dir.stat().st_ctime, tz=datetime.timezone.utc).isoformat(),
        })
    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return {"runs": entries}


@app.get("/runs/{run_id}/events")
async def stream_events(run_id: str):
    workspace = _workspace_for(run_id)  # 404s on an unknown run_id before opening a stream
    history = list(_EVENT_HISTORY.get(run_id) or load_persisted_events(workspace))
    manifest = _read_json_or_none(workspace / "output" / "run-manifest.json")
    if manifest is not None and not any(e.get("type") == "done" for e in history):
        history.append({
            "type": "done",
            "status": manifest["status"],
            "error_code": manifest.get("error_code"),
        })
    already_done = any(e["type"] == "done" for e in history)

    async def event_generator():
        for event in history:
            yield f"data: {json.dumps(event)}\n\n"
        if already_done:
            return
        queue: asyncio.Queue = asyncio.Queue()
        _EVENT_SUBSCRIBERS.setdefault(run_id, []).append(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] == "done":
                    break
        finally:
            _EVENT_SUBSCRIBERS.get(run_id, []).remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # A reverse proxy that gzips this stream also buffers it, so the
            # browser's EventSource receives nothing until the run ends and the
            # UI sits on "Working on it" for the whole run. `no-transform` tells
            # any intermediary not to re-encode the body; `X-Accel-Buffering`
            # covers nginx, which buffers proxied responses even uncompressed.
            # curl does not request gzip by default, so this only reproduces in
            # a browser.
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    workspace = _workspace_for(run_id)
    manifest = _read_json_or_none(workspace / "output" / "run-manifest.json")
    if manifest is not None:
        return {"run_id": run_id, "status": manifest["status"], "error_code": manifest.get("error_code")}

    _RUN_PHASES[run_id] = "cancelled"
    task = _RUN_TASKS.get(run_id)
    if task is not None and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    outcome = _persist_terminal_lifecycle(workspace, "cancelled", "run_cancelled")
    return {"run_id": run_id, **outcome}


@app.post("/runs/{run_id}/approve")
async def approve_run(run_id: str, payload: dict = Body(...)):
    """Persists the curator-edited record as a distinct artifact
    (approved-product.json) rather than overwriting canonical-product.json,
    so the raw agent draft and the human-approved version are never
    conflated -- 'only after the user approves should results be saved'
    means an approval produces a new artifact, not a silent edit in place."""
    workspace = _workspace_for(run_id)
    manifest_path = workspace / "output" / "run-manifest.json"
    manifest = _read_json_or_none(manifest_path)
    if manifest is None:
        raise HTTPException(status_code=409, detail="run has not finished")
    if manifest["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"cannot approve a run with status '{manifest['status']}'")

    fields = payload.get("fields")
    if not isinstance(fields, dict):
        raise HTTPException(status_code=400, detail="'fields' must be an object")

    approved_at = _now_iso()
    request = _read_json_or_none(workspace / "input" / "request.json") or {}
    approved_record = {
        "run_metadata": {"approved_at": approved_at, "source": "user-approved"},
        "product_type": request.get("product_type", "accommodation"),
        "fields": fields,
    }
    (workspace / "output" / "approved-product.json").write_text(
        json.dumps(approved_record, indent=2), encoding="utf-8")

    manifest["approved"] = True
    manifest["approved_at"] = approved_at
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"status": "approved", "approved_at": approved_at}


@app.get("/runs/{run_id}/artifacts/{name}")
async def get_artifact(run_id: str, name: str):
    if name not in ARTIFACT_NAMES:
        raise HTTPException(status_code=404, detail="unknown artifact name")
    workspace = _workspace_for(run_id)
    artifact_path = workspace / "output" / name
    if not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="artifact not produced by this run")
    # Without an explicit filename, FileResponse sends no Content-Disposition
    # header at all -- a browser download then has nothing to name the file
    # from and falls back to a bare temp-file id with no extension.
    return FileResponse(artifact_path, filename=name)


@app.delete("/runs/{run_id}", status_code=204)
async def delete_run(run_id: str):
    workspace = _workspace_for(run_id)
    task = _RUN_TASKS.pop(run_id, None)
    _RUN_PHASES.pop(run_id, None)
    if task is not None and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    shutil.rmtree(workspace, ignore_errors=True)
    return None





