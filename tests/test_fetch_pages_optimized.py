import importlib
import json
import sys

import httpx
import pytest

from conftest import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))
fetch_pages_optimized = importlib.import_module("fetch_pages_optimized")


@pytest.mark.asyncio
async def test_run_fetch_reuses_one_client_and_respects_concurrency(workspace, monkeypatch):
    active = 0
    maximum_active = 0
    factory_calls = 0

    class TrackingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, headers=None):
            nonlocal active, maximum_active
            active += 1
            maximum_active = max(maximum_active, active)
            await __import__("asyncio").sleep(0.02)
            active -= 1
            path = httpx.URL(url).path
            request = httpx.Request("GET", url)
            return httpx.Response(
                200,
                request=request,
                headers={"content-type": "text/html"},
                text=f"<html><body><p>Accommodation facts for unique page {path}.</p></body></html>",
            )

    def client_factory():
        nonlocal factory_calls
        factory_calls += 1
        return TrackingClient()

    monkeypatch.setattr(fetch_pages_optimized, "_build_async_client", client_factory)
    monkeypatch.setattr(fetch_pages_optimized, "is_private_or_unsafe_host", lambda _host: False)

    manifest_path = workspace / "work" / "source-manifest.json"
    manifest_path.write_text(json.dumps({
        "sources": [], "approved_domains": ["example.fi"], "next_source_id_index": 1,
    }), encoding="utf-8")
    result = await fetch_pages_optimized.run_fetch(
        manifest_path,
        workspace / "work" / "pages",
        workspace / "work" / "fetched-pages.json",
        [f"https://example.fi/page-{index}" for index in range(6)],
        concurrency=3,
    )

    assert result["fetched"] == 6
    assert factory_calls == 1
    assert maximum_active == 3


@pytest.mark.asyncio
async def test_link_details_and_budget_rejections_are_recorded(workspace, monkeypatch):
    html = """<html lang='fi'><head><title>Example stay</title></head><body><p>A sufficiently long accommodation description.</p>
    <nav><a href='/rooms'>Our rooms</a></nav><a href='https://outside.example/book'>Book</a>
    </body></html>"""
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, request=request, headers={"content-type": "text/html"}, text=html,
    ))
    monkeypatch.setattr(
        fetch_pages_optimized,
        "_build_async_client",
        lambda: httpx.AsyncClient(transport=transport, follow_redirects=False),
    )
    monkeypatch.setattr(fetch_pages_optimized, "is_private_or_unsafe_host", lambda _host: False)
    monkeypatch.setattr(fetch_pages_optimized, "MAX_URLS_PER_INVOCATION", 1)

    manifest_path = workspace / "work" / "source-manifest.json"
    manifest_path.write_text(json.dumps({
        "sources": [{"id": "p001", "type": "seed_url", "url": "https://example.fi/"}],
        "approved_domains": ["example.fi"], "next_source_id_index": 2,
    }), encoding="utf-8")
    result = await fetch_pages_optimized.run_fetch(
        manifest_path,
        workspace / "work" / "pages",
        workspace / "work" / "fetched-pages.json",
        ["https://example.fi/", "https://example.fi/second"],
    )

    assert result["budget_rejections"] == 1
    metadata = json.loads((workspace / "work" / "pages" / "p001.meta.json").read_text(encoding="utf-8"))
    assert metadata["internal_link_details"][0]["text"] == "Our rooms"
    assert metadata["internal_link_details"][0]["surrounding_text"] == "Our rooms"
    assert metadata["title"] == "Example stay"
    assert metadata["language_hint"] == "fi"
    assert metadata["retrieved_at"]
    assert metadata["content_bytes"] > 0
    stored_text = (workspace / "work" / "pages" / "p001.txt").read_text(encoding="utf-8")
    assert stored_text.startswith("[line 1]")
    index = json.loads((workspace / "work" / "fetched-pages.json").read_text(encoding="utf-8"))
    assert any(failure["reason"] == "invocation_page_budget_exceeded" for failure in index["failures"])


@pytest.mark.asyncio
async def test_redirect_target_is_revalidated_for_ssrf(monkeypatch):
    transport = httpx.MockTransport(lambda request: httpx.Response(
        302, request=request, headers={"location": "http://127.0.0.1/private"},
    ))
    monkeypatch.setattr(
        fetch_pages_optimized,
        "is_private_or_unsafe_host",
        lambda host: host == "127.0.0.1",
    )
    async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
        result = await fetch_pages_optimized.fetch_one_async(
            "https://example.fi/start", {"example.fi"}, client,
        )
    assert result["status"] == "rejected"
    assert result["reason"] == "redirect_to_unsafe_host"


@pytest.mark.asyncio
async def test_oversized_and_javascript_only_pages_remain_visible(monkeypatch):
    responses = {
        "/large": "<html><body>This response is intentionally too large.</body></html>",
        "/empty": "<html><body><script>renderApp()</script></body></html>",
    }
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200,
        request=request,
        headers={"content-type": "text/html"},
        text=responses[request.url.path],
    ))
    monkeypatch.setattr(fetch_pages_optimized, "is_private_or_unsafe_host", lambda _host: False)
    monkeypatch.setattr(fetch_pages_optimized, "MAX_PAGE_BYTES", 20)
    async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
        oversized = await fetch_pages_optimized.fetch_one_async(
            "https://example.fi/large", {"example.fi"}, client,
        )
        monkeypatch.setattr(fetch_pages_optimized, "MAX_PAGE_BYTES", 1024)
        js_only = await fetch_pages_optimized.fetch_one_async(
            "https://example.fi/empty", {"example.fi"}, client,
        )
    assert oversized["reason"] == "page_too_large"
    assert js_only["reason"] == "empty_or_js_only"


@pytest.mark.asyncio
async def test_duplicate_content_is_deduplicated_and_counted_once(workspace, monkeypatch):
    html = "<html><body><p>The same sufficiently long hotel description.</p></body></html>"
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, request=request, headers={"content-type": "text/html"}, text=html,
    ))
    monkeypatch.setattr(
        fetch_pages_optimized,
        "_build_async_client",
        lambda: httpx.AsyncClient(transport=transport, follow_redirects=False),
    )
    monkeypatch.setattr(fetch_pages_optimized, "is_private_or_unsafe_host", lambda _host: False)
    manifest_path = workspace / "work" / "source-manifest.json"
    manifest_path.write_text(json.dumps({
        "sources": [], "approved_domains": ["example.fi"], "next_source_id_index": 1,
    }), encoding="utf-8")

    result = await fetch_pages_optimized.run_fetch(
        manifest_path,
        workspace / "work" / "pages",
        workspace / "work" / "fetched-pages.json",
        ["https://example.fi/one", "https://example.fi/two"],
    )

    assert result["fetched"] == 1
    assert result["total_pages"] == 1
    assert result["total_content_bytes"] > 0


