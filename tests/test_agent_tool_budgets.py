import json

import pytest

import app.agent_tools as agent_tools
from app.telemetry import RunTelemetry
from conftest import PACKAGE_DIR


def test_evidence_budget_is_fair_across_sources():
    records = [
        {"source_id": "p001", "text": "a" * 30_000},
        {"source_id": "p002", "text": "b" * 30_000},
    ]
    included, limitations = agent_tools._bounded_evidence(records)
    assert [len(record["text"]) for record in included] == [20_000, 20_000]
    assert {item["source_id"] for item in limitations} == {"p001", "p002"}
    assert all(item["reason"] == "per_source_limit" for item in limitations)


def test_evidence_budget_is_global_across_tool_responses(workspace):
    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )
    first_records = [
        {"source_id": f"p{index:03d}", "text": "a" * size}
        for index, size in enumerate([20_000, 20_000, 20_000, 19_990], start=1)
    ]
    first, _limits = agent_tools._take_evidence_budget(state, first_records)
    second, limitations = agent_tools._take_evidence_budget(
        state, [{"source_id": "p002", "text": "b" * 20}],
    )

    assert sum(len(record["text"]) for record in first) == agent_tools.MAX_EVIDENCE_CHARS - 10
    assert len(second[0]["text"]) == 10
    assert limitations[0]["reason"] == "evidence_budget_exhausted"
    assert state.evidence_chars_returned == agent_tools.MAX_EVIDENCE_CHARS


def test_candidate_ranking_prefers_relevant_accommodation_links():
    generic = {"url": "https://example.fi/company", "anchor_text": "Company", "surrounding_text": ""}
    relevant = {"url": "https://example.fi/rooms", "anchor_text": "Hotel rooms", "surrounding_text": "Book accommodation"}
    assert agent_tools._candidate_score(relevant) > agent_tools._candidate_score(generic)


def test_candidates_exclude_urls_already_fetched(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("A sufficiently long page of hotel facts.", encoding="utf-8")
    (workspace / "work" / "pages" / "p001.meta.json").write_text(json.dumps({
        "internal_link_details": [
            {"text": "Home", "href": "https://example.fi/"},
            {"text": "Rooms", "href": "https://example.fi/rooms"},
        ],
    }), encoding="utf-8")
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({
        "pages": [{
            "id": "p001", "url": "https://example.fi/", "final_url": "https://example.fi/",
            "canonical_url": None, "content_hash": "one",
        }],
        "failures": [], "next_source_id_index": 2,
    }), encoding="utf-8")

    candidates = agent_tools._candidate_entries(workspace)
    assert [candidate["url"] for candidate in candidates] == ["https://example.fi/rooms"]


@pytest.mark.asyncio
async def test_total_page_budget_is_enforced_before_fetch(workspace):
    pages = []
    for index in range(1, agent_tools.MAX_TOTAL_PAGES + 1):
        source_id = f"p{index:03d}"
        (workspace / "work" / "pages" / f"{source_id}.txt").write_text(
            f"Stored accommodation facts for page {index}.", encoding="utf-8",
        )
        (workspace / "work" / "pages" / f"{source_id}.meta.json").write_text("{}", encoding="utf-8")
        pages.append({
            "id": source_id, "url": f"https://example.fi/{index}",
            "final_url": f"https://example.fi/{index}", "canonical_url": None,
            "content_hash": str(index),
        })
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({
        "pages": pages, "failures": [], "next_source_id_index": len(pages) + 1,
    }), encoding="utf-8")
    (workspace / "work" / "link-candidates.json").write_text(json.dumps({
        "links": [{"id": "l001", "url": "https://example.fi/extra"}],
    }), encoding="utf-8")

    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )
    state.prepared = True
    response = await state.handlers["fetch_selected_pages"]({
        "link_ids": ["l001"], "reason": "additional product page",
    })
    assert response["is_error"] is True
    assert "page_budget_exceeded" in response["content"][0]["text"]


@pytest.mark.asyncio
async def test_recovery_fetch_has_separate_small_budget(workspace):
    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )
    state.prepared = True
    state.expansion_calls = 1
    response = await state.handlers["fetch_selected_pages"]({
        "link_ids": [f"l{index:03d}" for index in range(1, agent_tools.MAX_RECOVERY_SELECTED + 2)],
        "reason": "unusual navigation recovery",
    })
    assert response["is_error"] is True
    assert "page_budget_exceeded" in response["content"][0]["text"]
