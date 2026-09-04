import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient

import app.api as api_module


async def _fake_completed_run(workspace, package_dir, env_bundle, on_event=None):
    if on_event:
        on_event({"type": "stage", "stage": "stage_1"})
    await asyncio.sleep(0.15)
    output_dir = workspace / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text("{}", encoding="utf-8")
    (output_dir / "canonical-product.json").write_text(json.dumps({
        "fields": {"name": {"fi": "Esimerkkihotelli", "en": "Example Hotel"}}
    }), encoding="utf-8")
    (output_dir / "result.xlsx").write_bytes(b"fake-xlsx")
    (output_dir / "review-report.md").write_text("# report", encoding="utf-8")
    (output_dir / "sources.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (output_dir / "run-manifest.json").write_text(json.dumps({
        "status": "completed", "error_code": None, "stage_reached": "stage_7",
    }), encoding="utf-8")
    outcome = {"status": "completed", "error_code": None}
    if on_event:
        on_event({"type": "done", **outcome})
    return outcome


async def _fake_slow_run(workspace, package_dir, env_bundle, on_event=None):
    await asyncio.sleep(1.0)
    return {"status": "completed", "error_code": None}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module, "WORKSPACE_BASE", tmp_path / "runs")
    monkeypatch.setattr(api_module, "load_foundry_env", lambda *a, **k: {"env": {}, "model": "claude-sonnet-5"})
    monkeypatch.setattr(api_module, "run_analysis", _fake_completed_run)
    with TestClient(api_module.app) as c:
        yield c


def test_missing_website_urls_field_is_rejected(client):
    # Absent entirely -> FastAPI's own Form(...) validation (422), before our
    # handler runs at all. Present-but-blank is the 400 case we own; see below.
    resp = client.post("/runs", data={})
    assert resp.status_code == 422


def test_blank_website_urls_are_rejected(client):
    resp = client.post("/runs", data={"website_urls": ["   "]})
    assert resp.status_code == 400


def test_create_run_returns_202_and_run_id(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    assert resp.status_code == 202
    body = resp.json()
    assert "run_id" in body and len(body["run_id"]) > 0


def test_get_run_unknown_id_returns_404(client):
    resp = client.get("/runs/does-not-exist")
    assert resp.status_code == 404


def test_get_run_reaches_completed_status(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]

    time.sleep(0.4)  # let the fake background task finish (real sub-second wait, no live calls)

    status_resp = client.get(f"/runs/{run_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] == "completed"
    assert body["error_code"] is None
    assert body["stage_reached"] == "stage_7"
    assert "result.json" in body["artifacts"]
    assert "run-manifest.json" in body["artifacts"]
    assert "sources.json" in body["artifacts"]


def test_get_artifact_returns_file_content(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    artifact_resp = client.get(f"/runs/{run_id}/artifacts/result.json")
    assert artifact_resp.status_code == 200
    assert artifact_resp.json() == {}

    sources_resp = client.get(f"/runs/{run_id}/artifacts/sources.json")
    assert sources_resp.status_code == 200
    assert sources_resp.json() == {"sources": []}


def test_get_artifact_unknown_name_returns_404(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    artifact_resp = client.get(f"/runs/{run_id}/artifacts/../../etc/passwd")
    assert artifact_resp.status_code == 404


def test_get_artifact_not_yet_produced_returns_404(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    # scope-decision.json is a valid artifact name but wasn't produced by this fake completed run
    artifact_resp = client.get(f"/runs/{run_id}/artifacts/scope-decision.json")
    assert artifact_resp.status_code == 404


def test_run_id_path_traversal_is_rejected(client):
    resp = client.get("/runs/..%2F..%2Fetc")
    assert resp.status_code == 404


def test_delete_run_removes_workspace(client, tmp_path):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]

    del_resp = client.delete(f"/runs/{run_id}")
    assert del_resp.status_code == 204
    assert not (tmp_path / "runs" / run_id).exists()

    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 404


def test_get_run_while_still_running_reports_running(client, monkeypatch):
    monkeypatch.setattr(api_module, "run_analysis", _fake_slow_run)
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]

    status_resp = client.get(f"/runs/{run_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] == "running"
    # Regression: a frontend client does `d.artifacts.includes(...)`
    # unconditionally: these keys must exist for every status, not just once
    # a manifest is written, or an in-progress run crashes the caller.
    assert body["artifacts"] == []
    assert body["error_code"] is None
    assert body["stage_reached"] is None


def test_list_runs_includes_created_run(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    list_resp = client.get("/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()["runs"]
    matching = [r for r in runs if r["run_id"] == run_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "completed"
    assert matching[0]["website_urls"] == ["https://example.fi"]
    assert matching[0]["product_name"] == "Example Hotel"
    assert matching[0]["approved"] is False


def test_list_runs_newest_first(client):
    first = client.post("/runs", data={"website_urls": ["https://example.fi"]}).json()["run_id"]
    time.sleep(0.05)
    second = client.post("/runs", data={"website_urls": ["https://other.fi"]}).json()["run_id"]
    time.sleep(0.4)

    runs = client.get("/runs").json()["runs"]
    ids_in_order = [r["run_id"] for r in runs if r["run_id"] in (first, second)]
    assert ids_in_order == [second, first]


def test_category_taxonomy_is_filtered_by_product_type(client):
    accommodation_resp = client.get("/taxonomy/categories", params={"product_type": "accommodation"})
    shops_resp = client.get("/taxonomy/categories", params={"product_type": "shops"})

    assert accommodation_resp.status_code == 200
    assert shops_resp.status_code == 200
    accommodation = accommodation_resp.json()
    shops = shops_resp.json()
    accommodation_ids = {category["id"] for category in accommodation["categories"]}
    shops_ids = {category["id"] for category in shops["categories"]}
    assert accommodation["taxonomy_version"]
    assert accommodation["product_type"] == "accommodation"
    assert shops["product_type"] == "shops"
    assert "hotel" in accommodation_ids
    assert "shopping_center" not in accommodation_ids
    assert "shopping_center" in shops_ids
    assert "hotel" not in shops_ids
    assert all(category["group"] == "accommodation" for category in accommodation["categories"])
    assert all(category["group"] == "shops" for category in shops["categories"])


def test_category_taxonomy_rejects_unknown_product_type(client):
    resp = client.get("/taxonomy/categories", params={"product_type": "restaurants"})
    assert resp.status_code == 400


@pytest.mark.parametrize(
    ("product_type", "valid_category", "invalid_category"),
    [
        ("accommodation", "hotel", "shopping_center"),
        ("shops", "shopping_center", "hotel"),
    ],
)
def test_approve_validates_categories_for_product_type(
    client, product_type, valid_category, invalid_category,
):
    resp = client.post(
        "/runs",
        data={"website_urls": ["https://example.fi"], "product_type": product_type},
    )
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    invalid_resp = client.post(
        f"/runs/{run_id}/approve",
        json={"fields": {"categories": [invalid_category]}},
    )
    assert invalid_resp.status_code == 400
    assert invalid_category in invalid_resp.json()["detail"]["invalid_categories"]

    valid_resp = client.post(
        f"/runs/{run_id}/approve",
        json={"fields": {"categories": [valid_category]}},
    )
    assert valid_resp.status_code == 200
    approved = client.get(f"/runs/{run_id}/artifacts/approved-product.json").json()
    assert approved["fields"]["categories"] == [valid_category]


def test_approve_rejects_duplicate_categories(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    approve_resp = client.post(
        f"/runs/{run_id}/approve",
        json={"fields": {"categories": ["hotel", "hotel"]}},
    )
    assert approve_resp.status_code == 400


def test_approve_persists_edited_fields_as_new_artifact(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    edited = {"fields": {"name": {"fi": "Muokattu nimi"}, "capacity": {"rooms": 5}}}
    approve_resp = client.post(f"/runs/{run_id}/approve", json=edited)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    artifact_resp = client.get(f"/runs/{run_id}/artifacts/approved-product.json")
    assert artifact_resp.status_code == 200
    stored = artifact_resp.json()
    assert stored["fields"] == edited["fields"]
    assert stored["run_metadata"]["source"] == "user-approved"

    manifest_resp = client.get(f"/runs/{run_id}/artifacts/run-manifest.json")
    assert manifest_resp.json()["approved"] is True

    summary = next(r for r in client.get("/runs").json()["runs"] if r["run_id"] == run_id)
    assert summary["product_name"] == "Muokattu nimi"


def test_approve_before_run_finishes_is_rejected(client, monkeypatch):
    monkeypatch.setattr(api_module, "run_analysis", _fake_slow_run)
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]

    approve_resp = client.post(f"/runs/{run_id}/approve", json={"fields": {}})
    assert approve_resp.status_code == 409


def test_approve_rejects_non_object_fields(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    approve_resp = client.post(f"/runs/{run_id}/approve", json={"fields": "not-an-object"})
    assert approve_resp.status_code == 400


def test_events_stream_replays_history_then_done(client):
    resp = client.post("/runs", data={"website_urls": ["https://example.fi"]})
    run_id = resp.json()["run_id"]
    time.sleep(0.4)

    with client.stream("GET", f"/runs/{run_id}/events") as stream_resp:
        assert stream_resp.status_code == 200
        body = "".join(stream_resp.iter_text())

    assert '"type": "stage"' in body
    assert '"type": "done"' in body


def test_events_stream_unknown_run_id_returns_404(client):
    resp = client.get("/runs/does-not-exist/events")
    assert resp.status_code == 404


def test_create_shops_run_persists_and_returns_product_type(client):
    resp = client.post(
        "/runs",
        data={"website_urls": ["https://example.fi/shop"], "product_type": "shops"},
    )
    assert resp.status_code == 202
    run_id = resp.json()["run_id"]

    request = json.loads(
        (api_module.WORKSPACE_BASE / run_id / "input" / "request.json").read_text(encoding="utf-8")
    )
    assert request["product_type"] == "shops"

    time.sleep(0.4)
    detail = client.get(f"/runs/{run_id}").json()
    assert detail["product_type"] == "shops"

    summary = next(r for r in client.get("/runs").json()["runs"] if r["run_id"] == run_id)
    assert summary["product_type"] == "shops"

    approve_resp = client.post(f"/runs/{run_id}/approve", json={"fields": {}})
    assert approve_resp.status_code == 200
    approved = client.get(f"/runs/{run_id}/artifacts/approved-product.json").json()
    assert approved["product_type"] == "shops"


def test_create_run_rejects_unknown_product_type(client):
    resp = client.post(
        "/runs",
        data={"website_urls": ["https://example.fi"], "product_type": "restaurants"},
    )
    assert resp.status_code == 400
