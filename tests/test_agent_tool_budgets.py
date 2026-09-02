import json

import pytest

import app.agent_tools as agent_tools
from app.telemetry import RunTelemetry
from conftest import PACKAGE_DIR


def test_evidence_is_split_losslessly_across_sources():
    records = [
        {"source_id": "p001", "text": "a" * 30_000},
        {"source_id": "p002", "text": "b" * 30_000},
    ]
    items = agent_tools._evidence_context_items(records)

    assert "".join(item["text"] for item in items if item["source_id"] == "p001") == "a" * 30_000
    assert "".join(item["text"] for item in items if item["source_id"] == "p002") == "b" * 30_000
    assert all(len(item["text"]) <= agent_tools.MAX_EVIDENCE_CHUNK_CHARS for item in items)


def test_context_pages_are_bounded_and_preserve_all_text(workspace):
    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )
    records = [
        {"source_id": f"p{index:03d}", "text": "a" * size}
        for index, size in enumerate([20_000, 20_000, 20_000, 19_990], start=1)
    ]
    first_cursor, page_count, evidence_chars, candidate_count = agent_tools._queue_context_pages(
        state, records, [],
    )

    assert first_cursor == "ctx0001"
    assert page_count > 1
    assert evidence_chars == 79_990
    assert candidate_count == 0
    delivered = "".join(
        item["text"]
        for cursor in state.pending_context_cursors
        for item in state.context_pages[cursor]["evidence"]
    )
    assert delivered == "".join(record["text"] for record in records)
    assert all(
        len(json.dumps(state.context_pages[cursor], ensure_ascii=False)) < agent_tools.MAX_CONTEXT_PAGE_CHARS + 1_000
        for cursor in state.pending_context_cursors
    )


def test_context_projection_removes_duplicate_links_and_tracking_parameters():
    records = [{
        "source_id": "p001",
        "source_type": "website",
        "url": "https://example.fi/hotel?utm_source=x&room=2#g",
        "text": "Complete hotel evidence.",
        "internal_links": [{"href": "https://example.fi/contact"}],
        "external_links": [{"href": "https://other.example/"}],
    }]

    item = agent_tools._evidence_context_items(records)[0]

    assert item["url"] == "https://example.fi/hotel?room=2"
    assert "internal_links" not in item
    assert "external_links" not in item


def test_document_flat_text_is_preserved_without_duplicate_segments():
    text = "First paragraph.\n\nSecond paragraph with a table value."
    records = [{
        "source_id": "d001",
        "source_type": "document",
        "file_name": "hotel.pdf",
        "parsing_method": "test",
        "segments": [{"locator": "page 1", "text": text}],
        "text": text,
    }]

    items = agent_tools._evidence_context_items(records)

    assert "".join(item["text"] for item in items) == text
    assert all("segments" not in item for item in items)


def test_all_candidate_links_are_paginated_instead_of_capped(workspace):
    links = [
        {"text": f"Hotel page {index}", "href": f"https://example.fi/hotel/{index}"}
        for index in range(150)
    ]
    (workspace / "work" / "pages" / "p001.txt").write_text("Hotel facts", encoding="utf-8")
    (workspace / "work" / "pages" / "p001.meta.json").write_text(json.dumps({
        "internal_link_details": links,
    }), encoding="utf-8")
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({
        "pages": [{"id": "p001", "url": "https://example.fi/", "final_url": "https://example.fi/"}],
        "failures": [],
    }), encoding="utf-8")

    candidates = agent_tools._candidate_entries(workspace)

    assert len(candidates) == 150


def test_total_context_budget_fails_instead_of_truncating(workspace, monkeypatch):
    monkeypatch.setattr(agent_tools, "MAX_TOTAL_CONTEXT_CHARS", 100)
    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )

    with pytest.raises(ValueError, match="model_context_budget_exceeded"):
        agent_tools._queue_context_pages(
            state,
            [{"source_id": "p001", "source_type": "website", "text": "x" * 500}],
            [],
        )

    assert state.pending_context_cursors == []


@pytest.mark.asyncio
async def test_scandic_sized_context_is_delivered_losslessly_below_transport_guard(workspace):
    _server, state, _allowed = agent_tools.build_optimized_tool_server(
        workspace, PACKAGE_DIR, RunTelemetry("test"),
    )
    state.prepared = True
    text = ("Scandic Grand Central Helsinki accommodation evidence.\n" * 28_000)[:1_400_000]
    candidates = [{
        "id": f"l{index:03d}",
        "url": f"https://example.fi/hotel/{index}?utm_source=campaign&gclid={'x' * 300}",
        "anchor_text": f"Hotel information {index}",
        "surrounding_text": "Rooms, accessibility, sustainability and booking information.",
        "discovered_on": "p001",
    } for index in range(1, 88)]
    cursor, page_count, evidence_chars, candidate_count = agent_tools._queue_context_pages(
        state,
        [{"source_id": "p001", "source_type": "website", "url": "https://example.fi/", "text": text}],
        candidates,
    )

    delivered_text = ""
    delivered_candidates = []
    response_count = 0
    while cursor:
        response = await state.handlers["read_context_page"]({"cursor": cursor})
        assert response["is_error"] is False
        assert len(response["content"][0]["text"]) <= agent_tools.MAX_MCP_RESPONSE_CHARS
        payload = json.loads(response["content"][0]["text"])
        delivered_text += "".join(item["text"] for item in payload["evidence"])
        delivered_candidates.extend(payload["candidate_links"])
        cursor = payload["next_cursor"]
        response_count += 1

    assert response_count == page_count
    assert evidence_chars == len(text)
    assert candidate_count == 87
    assert delivered_text == text
    assert len(delivered_candidates) == 87
    assert all("utm_source" not in candidate["url"] for candidate in delivered_candidates)
    assert state.pending_context_cursors == []
    delivery = json.loads((workspace / "work" / "context-delivery.json").read_text(encoding="utf-8"))
    assert delivery["complete"] is True
    assert delivery["pages_delivered"] == page_count


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
