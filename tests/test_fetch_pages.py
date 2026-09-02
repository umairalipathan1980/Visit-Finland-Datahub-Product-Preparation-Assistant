import importlib
import json
import sys

import httpx
import pytest

from conftest import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))
fetch_pages = importlib.import_module("fetch_pages")


# --- pure normalization tests (no network at all) ---

def test_trailing_slash_is_normalized():
    a = fetch_pages.normalize_url("https://example.fi/majoitus")
    b = fetch_pages.normalize_url("https://example.fi/majoitus/")
    assert a == b


def test_lang_query_param_is_preserved_and_distinguishes_pages():
    fi = fetch_pages.normalize_url("https://example.fi/majoitus?lang=fi")
    en = fetch_pages.normalize_url("https://example.fi/majoitus?lang=en")
    assert fi != en


def test_tracking_params_are_stripped():
    url = fetch_pages.normalize_url("https://example.fi/majoitus?utm_source=fb&fbclid=abc&gclid=xyz&mc_cid=q")
    assert url == "https://example.fi/majoitus"


def test_unrecognized_param_is_preserved():
    url = fetch_pages.normalize_url("https://example.fi/room?roomId=42")
    assert "roomId=42" in url


def test_param_order_does_not_produce_two_candidates():
    a = fetch_pages.normalize_url("https://example.fi/x?b=2&a=1")
    b = fetch_pages.normalize_url("https://example.fi/x?a=1&b=2")
    assert a == b


def test_fragment_is_stripped():
    assert "#" not in fetch_pages.normalize_url("https://example.fi/page#section")


def test_host_and_scheme_are_lowercased():
    assert fetch_pages.normalize_url("HTTPS://Example.FI/Path") == "https://example.fi/Path"


def test_registrable_domain_heuristic():
    assert fetch_pages.registrable_domain("sub.example.fi") == "example.fi"
    assert fetch_pages.registrable_domain("example.fi") == "example.fi"


def test_localhost_is_unsafe_host():
    assert fetch_pages.is_private_or_unsafe_host("localhost") is True


def test_public_domain_is_not_flagged_unsafe():
    # example.com is an IANA-reserved documentation domain, guaranteed to resolve
    # to a public address; this is the one place these tests touch DNS.
    assert fetch_pages.is_private_or_unsafe_host("example.com") is False


# --- fetch_one / main() with a mocked transport: no real network traffic ---

HTML_WITH_LINKS_AND_CANONICAL = """
<html><head><link rel="canonical" href="https://example.fi/majoitus"></head>
<body><p>Esimerkkihotelli tarjoaa 42 huonetta keskustassa Helsingissä.</p>
<a href="/yhteystiedot?utm_source=x">Yhteystiedot</a>
<a href="https://booking.example.fi/x">Booking</a>
<a href="https://external.invalid/other">External</a>
</body></html>
"""


def make_mock_transport(responses: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in responses:
            return responses[url]
        return httpx.Response(404, text="not found")
    return httpx.MockTransport(handler)


@pytest.fixture
def mock_html_response(monkeypatch):
    def _install(url_to_html: dict[str, str]):
        responses = {
            url: httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html)
            for url, html in url_to_html.items()
        }
        transport = make_mock_transport(responses)
        monkeypatch.setattr(fetch_pages, "_build_client",
                             lambda: httpx.Client(transport=transport, follow_redirects=False))
    return _install


def run_main(args):
    old_argv = sys.argv
    sys.argv = ["fetch_pages.py"] + args
    try:
        return fetch_pages.main()
    finally:
        sys.argv = old_argv


def test_fetch_stores_text_hash_canonical_and_links(workspace, mock_html_response):
    mock_html_response({"https://example.fi/": HTML_WITH_LINKS_AND_CANONICAL})
    manifest = {
        "sources": [{"id": "p001", "type": "seed_url", "url": "https://example.fi/"}],
        "approved_domains": ["example.fi"],
        "next_source_id_index": 2,
    }
    (workspace / "work" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    rc = run_main([
        "--manifest", str(workspace / "work" / "source-manifest.json"),
        "--pages-dir", str(workspace / "work" / "pages"),
        "--output", str(workspace / "work" / "fetched-pages.json"),
    ])
    assert rc == 0
    page_text = (workspace / "work" / "pages" / "p001.txt").read_text(encoding="utf-8")
    assert "42 huonetta" in page_text

    meta = json.loads((workspace / "work" / "pages" / "p001.meta.json").read_text(encoding="utf-8"))
    assert meta["canonical_url"] == "https://example.fi/majoitus"
    # booking.example.fi is a subdomain of the approved domain -> internal, a fetch candidate
    assert "https://booking.example.fi/x" in meta["internal_links"]
    # external.invalid is off-domain -> recorded, but never a fetch candidate
    assert any("external.invalid" in link for link in meta["external_links"])
    assert not any("external.invalid" in link for link in meta["internal_links"])
    assert not any("utm_source" in link for link in meta["internal_links"] + meta["external_links"])

    # The external link's URL is still quotable from the stored page text,
    # so it can be cited as e.g. booking_url evidence without ever fetching
    # or citing content from external.invalid itself.
    page_text = (workspace / "work" / "pages" / "p001.txt").read_text(encoding="utf-8")
    assert "https://external.invalid/other" in page_text
    assert "https://booking.example.fi/x" in page_text


def test_redirect_to_trailing_slash_does_not_loop(workspace, monkeypatch):
    """Regression: a bare-path request 301-redirected to its own slash-terminated
    form (the ordinary WordPress permalink pattern) must resolve in one hop.
    normalize_url would strip that trailing slash right back off, requesting
    the bare path again and looping until too_many_redirects."""
    html = "<html><body><p>Hangon maatilamajoitus tarjoaa majoitusta koko perheelle.</p></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://example.fi/yritys":
            return httpx.Response(301, headers={"location": "https://example.fi/yritys/"})
        if url == "https://example.fi/yritys/":
            return httpx.Response(200, headers={"content-type": "text/html"}, text=html)
        return httpx.Response(404, text="not found")

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(fetch_pages, "_build_client", lambda: httpx.Client(transport=transport, follow_redirects=False))

    result = fetch_pages.fetch_one("https://example.fi/yritys", {"example.fi"})
    assert result["status"] == "fetched"
    assert result["final_url"] == "https://example.fi/yritys/"


def test_domain_not_approved_is_rejected(workspace, mock_html_response):
    mock_html_response({"https://other.fi/": "<html><body>hi</body></html>"})
    manifest = {"sources": [], "approved_domains": ["example.fi"], "next_source_id_index": 1}
    (workspace / "work" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    rc = run_main([
        "--manifest", str(workspace / "work" / "source-manifest.json"),
        "--pages-dir", str(workspace / "work" / "pages"),
        "--output", str(workspace / "work" / "fetched-pages.json"),
        "--url", "https://other.fi/",
    ])
    assert rc == 0
    index = json.loads((workspace / "work" / "fetched-pages.json").read_text(encoding="utf-8"))
    assert index["pages"] == []
    assert index["failures"][0]["reason"] == "domain_not_approved"


def test_identical_content_hash_collapses_to_one_source(workspace, mock_html_response):
    html = "<html><body><p>Sama sisältö molemmilla sivuilla.</p></body></html>"
    mock_html_response({
        "https://example.fi/a": html,
        "https://example.fi/b": html,
    })
    manifest = {"sources": [], "approved_domains": ["example.fi"], "next_source_id_index": 1}
    (workspace / "work" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    run_main([
        "--manifest", str(workspace / "work" / "source-manifest.json"),
        "--pages-dir", str(workspace / "work" / "pages"),
        "--output", str(workspace / "work" / "fetched-pages.json"),
        "--url", "https://example.fi/a", "--url", "https://example.fi/b",
    ])
    index = json.loads((workspace / "work" / "fetched-pages.json").read_text(encoding="utf-8"))
    assert len(index["pages"]) == 1


def test_same_canonical_different_content_keeps_both(workspace, mock_html_response):
    html_fi = '<html><head><link rel="canonical" href="https://example.fi/x"></head><body>Tämä sivu on suomeksi kirjoitettu.</body></html>'
    html_en = '<html><head><link rel="canonical" href="https://example.fi/x"></head><body>This page is written in English.</body></html>'
    mock_html_response({
        "https://example.fi/x?lang=fi": html_fi,
        "https://example.fi/x?lang=en": html_en,
    })
    manifest = {"sources": [], "approved_domains": ["example.fi"], "next_source_id_index": 1}
    (workspace / "work" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    run_main([
        "--manifest", str(workspace / "work" / "source-manifest.json"),
        "--pages-dir", str(workspace / "work" / "pages"),
        "--output", str(workspace / "work" / "fetched-pages.json"),
        "--url", "https://example.fi/x?lang=fi", "--url", "https://example.fi/x?lang=en",
    ])
    index = json.loads((workspace / "work" / "fetched-pages.json").read_text(encoding="utf-8"))
    assert len(index["pages"]) == 2
