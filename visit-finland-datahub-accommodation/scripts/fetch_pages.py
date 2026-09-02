#!/usr/bin/env python3
"""Stage 3: the only script permitted to make outbound HTTP requests.

Retrieves pages and stores extracted text plus a links section under
work/pages/, splitting outbound links into internal (same registrable
domain -- candidates for the agent's expansion pass) and external (never
fetched, but their href is still quotable text on the page that links to
them). Computes a content hash plus rel="canonical" target for
post-retrieval dedup. Treats all retrieved content strictly as data --
nothing here is ever executed or interpreted as instructions.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

import httpx
from bs4 import BeautifulSoup

MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 3
REQUEST_TIMEOUT_S = 15.0
TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid"}


def is_private_or_unsafe_host(host: str) -> bool:
    try:
        addrs = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return True
    for addr in addrs:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return True
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified
            or str(ip) == "169.254.169.254"
        ):
            return True
    return False


def registrable_domain(host: str) -> str:
    labels = host.lower().rstrip(".").split(".")
    if len(labels) <= 2:
        return ".".join(labels)
    return ".".join(labels[-2:])


def normalize_url(raw_url: str, base: str | None = None) -> str | None:
    """Conservative normalization per plan Section 6 Stage 3.

    Strips fragment; lower-cases scheme/host; normalizes trailing slash;
    drops known tracking params; preserves everything else (lang, locale,
    hl, product/page IDs); sorts surviving params.
    """
    url = urljoin(base, raw_url) if base else raw_url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.hostname:
        return None

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
        if path == "":
            path = "/"

    kept_params = []
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        if k in TRACKING_PARAMS or any(k.startswith(p) for p in TRACKING_PARAM_PREFIXES):
            continue
        kept_params.append((k, v))
    kept_params.sort()
    query = urlencode(kept_params)

    return urlunparse((scheme, f"{host}{port}", path, "", query, ""))


def extract_text_and_links(html: str, page_url: str) -> tuple[str, list[dict], str | None]:
    """Returns (visible_text, links, canonical_url). Each link is
    {"text": anchor text, "href": raw href} -- the anchor text is kept
    alongside the href so a stored Links section (see fetch_one) can render
    both, which is what makes a link's URL a quotable, citable value."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    links = []
    for a in soup.find_all("a", href=True):
        links.append({"text": a.get_text(strip=True), "href": a["href"]})

    canonical = None
    link_tag = soup.find("link", rel=lambda v: v and "canonical" in v.lower() if isinstance(v, str) else "canonical" in (v or []))
    if link_tag and link_tag.get("href"):
        canonical = normalize_url(link_tag["href"], base=page_url)

    return text, links, canonical


def resolve_redirect_location(location: str, base: str) -> str | None:
    """Absolute-ize a redirect Location header without candidate-identity
    normalization. Stripping a trailing slash here (as normalize_url does for
    deduplication purposes) would fight a server that 301s the bare path to
    its own slash-terminated canonical form -- request A, get redirected to
    A/, "normalize" back to A, request A again: an infinite loop against any
    ordinary WordPress-style permalink redirect. Following a redirect must
    use the literal target the server named, not our own dedup opinion of it.
    """
    url = urljoin(base, location)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))


def _build_client() -> httpx.Client:
    """Isolated so tests can substitute a MockTransport without touching the network."""
    return httpx.Client(follow_redirects=False, timeout=REQUEST_TIMEOUT_S)


def fetch_one(url: str, approved_domains: set[str]) -> dict:
    parsed = urlparse(url)
    if is_private_or_unsafe_host(parsed.hostname or ""):
        return {"url": url, "status": "rejected", "reason": "unsafe_host"}
    if registrable_domain(parsed.hostname or "") not in approved_domains:
        return {"url": url, "status": "rejected", "reason": "domain_not_approved"}

    current_url = url
    redirects = 0
    try:
        with _build_client() as client:
            while True:
                resp = client.get(current_url, headers={"User-Agent": "VisitFinlandDataHubAssistant/0.1 (+poc)"})
                if resp.is_redirect:
                    redirects += 1
                    if redirects > MAX_REDIRECTS:
                        return {"url": url, "status": "rejected", "reason": "too_many_redirects"}
                    next_url = resolve_redirect_location(resp.headers.get("location", ""), base=current_url)
                    if not next_url:
                        return {"url": url, "status": "rejected", "reason": "invalid_redirect_target"}
                    next_parsed = urlparse(next_url)
                    if is_private_or_unsafe_host(next_parsed.hostname or ""):
                        return {"url": url, "status": "rejected", "reason": "redirect_to_unsafe_host"}
                    if registrable_domain(next_parsed.hostname or "") not in approved_domains:
                        return {"url": url, "status": "rejected", "reason": "redirect_leaves_approved_domain"}
                    current_url = next_url
                    continue
                break
    except httpx.HTTPError as exc:
        return {"url": url, "status": "unreachable", "reason": type(exc).__name__}

    if len(resp.content) > MAX_PAGE_BYTES:
        return {"url": url, "status": "rejected", "reason": "page_too_large", "http_status": resp.status_code}

    if resp.status_code >= 400:
        return {"url": url, "status": "unreachable", "reason": f"http_{resp.status_code}", "http_status": resp.status_code}

    content_type = resp.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        return {"url": url, "status": "rejected", "reason": f"non_html_content_type:{content_type}"}

    text, raw_links, canonical = extract_text_and_links(resp.text, current_url)
    if len(text) < 20:
        return {"url": url, "status": "unreachable", "reason": "empty_or_js_only", "http_status": resp.status_code}

    # Internal links (same registrable domain) are candidates for Stage 3's
    # second fetch. External links are never fetched and never a citable
    # source in their own right -- but the literal href is still evidence
    # about *this* page (the approved one we did fetch), same as any other
    # sentence on it. So both are recorded, and both hrefs are appended to
    # the stored text below, making them quotable for a field like
    # booking_url without ever retrieving or citing the destination's content.
    internal_links, external_links, seen = [], [], set()
    for link in raw_links:
        norm = normalize_url(link["href"], base=current_url)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        entry = {"text": link["text"][:200], "href": norm}
        link_host = urlparse(norm).hostname or ""
        if registrable_domain(link_host) in approved_domains:
            internal_links.append(entry)
        else:
            external_links.append(entry)

    stored_text = text
    all_links = internal_links + external_links
    if all_links:
        link_lines = "\n".join(f"{e['text'] or '(no link text)'} -> {e['href']}" for e in all_links)
        stored_text = f"{text}\n\n--- LINKS ---\n{link_lines}"

    content_hash = hashlib.sha256(stored_text.encode("utf-8")).hexdigest()

    return {
        "url": url,
        "final_url": current_url,
        "status": "fetched",
        "http_status": resp.status_code,
        "text": stored_text,
        "internal_links": [e["href"] for e in internal_links],
        "external_links": [e["href"] for e in external_links],
        "canonical_url": canonical,
        "content_hash": content_hash,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--pages-dir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--url", action="append", default=[], dest="urls")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    approved_domains = set(manifest.get("approved_domains", []))

    pages_dir = Path(args.pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output)

    if output_path.exists():
        index = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        index = {"pages": [], "failures": [], "next_source_id_index": manifest["next_source_id_index"]}

    existing_by_url = {p["url"]: p for p in index["pages"]}
    existing_hashes = {p["content_hash"] for p in index["pages"]}
    existing_canonical_by_hash = {p["content_hash"]: p.get("canonical_url") for p in index["pages"]}

    seed_url_to_id = {s["url"]: s["id"] for s in manifest["sources"] if s["type"] == "seed_url"}

    urls_to_fetch = list(args.urls) if args.urls else [s["url"] for s in manifest["sources"] if s["type"] == "seed_url"]

    fetched_count = 0
    for url in urls_to_fetch:
        norm_url = normalize_url(url) or url
        if norm_url in existing_by_url:
            continue  # already retrieved this run

        result = fetch_one(url, approved_domains)
        if result["status"] != "fetched":
            index["failures"].append({k: v for k, v in result.items() if k != "text"})
            continue

        if result["content_hash"] in existing_hashes:
            continue  # identical bytes already stored under another URL/id -- true duplicate

        source_id = seed_url_to_id.get(url) or seed_url_to_id.get(norm_url) or f"p{index['next_source_id_index']:03d}"
        if source_id not in seed_url_to_id.values():
            index["next_source_id_index"] += 1

        (pages_dir / f"{source_id}.txt").write_text(result["text"], encoding="utf-8")
        meta = {
            "source_id": source_id,
            "url": url,
            "final_url": result["final_url"],
            "http_status": result["http_status"],
            "content_hash": result["content_hash"],
            "canonical_url": result["canonical_url"],
            "internal_links": result["internal_links"],
            "external_links": result["external_links"],
        }
        (pages_dir / f"{source_id}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        index["pages"].append({
            "id": source_id,
            "url": url,
            "final_url": result["final_url"],
            "http_status": result["http_status"],
            "content_hash": result["content_hash"],
            "canonical_url": result["canonical_url"],
        })
        existing_by_url[norm_url] = index["pages"][-1]
        existing_hashes.add(result["content_hash"])
        fetched_count += 1

    output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "fetched": fetched_count, "failures": len(index["failures"]), "total_pages": len(index["pages"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
