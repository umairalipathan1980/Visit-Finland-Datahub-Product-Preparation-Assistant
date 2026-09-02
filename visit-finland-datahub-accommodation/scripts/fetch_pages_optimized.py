#!/usr/bin/env python3
"""Bounded concurrent retriever used by the coarse-tool workflow.

It preserves fetch_pages.py's artifact contract and security checks while
using one pooled AsyncClient for the entire invocation.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from fetch_pages import (
    MAX_PAGE_BYTES,
    MAX_REDIRECTS,
    REQUEST_TIMEOUT_S,
    extract_text_and_links,
    is_private_or_unsafe_host,
    normalize_url,
    registrable_domain,
    resolve_redirect_location,
)
from domain_utils import registrable_domain

MAX_CONCURRENT_FETCHES = 5
MAX_URLS_PER_INVOCATION = 25
TOTAL_FETCH_TIMEOUT_S = 60.0
USER_AGENT = "VisitFinlandDataHubAssistant/0.2 (+poc)"


def _build_async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=False, timeout=REQUEST_TIMEOUT_S)


def add_line_locators(text: str) -> str:
    return "\n".join(
        f"[line {index}] {line}"
        for index, line in enumerate(text.splitlines(), start=1)
    )


async def fetch_one_async(url: str, approved_domains: set[str], client: httpx.AsyncClient) -> dict:
    parsed = urlparse(url)
    if is_private_or_unsafe_host(parsed.hostname or ""):
        return {"url": url, "status": "rejected", "reason": "unsafe_host"}
    if registrable_domain(parsed.hostname or "") not in approved_domains:
        return {"url": url, "status": "rejected", "reason": "domain_not_approved"}

    current_url = url
    redirects = 0
    try:
        while True:
            response = await client.get(current_url, headers={"User-Agent": USER_AGENT})
            if not response.is_redirect:
                break
            redirects += 1
            if redirects > MAX_REDIRECTS:
                return {"url": url, "status": "rejected", "reason": "too_many_redirects"}
            next_url = resolve_redirect_location(response.headers.get("location", ""), base=current_url)
            if not next_url:
                return {"url": url, "status": "rejected", "reason": "invalid_redirect_target"}
            next_parsed = urlparse(next_url)
            if is_private_or_unsafe_host(next_parsed.hostname or ""):
                return {"url": url, "status": "rejected", "reason": "redirect_to_unsafe_host"}
            if registrable_domain(next_parsed.hostname or "") not in approved_domains:
                return {"url": url, "status": "rejected", "reason": "redirect_leaves_approved_domain"}
            current_url = next_url
    except httpx.HTTPError as exc:
        return {"url": url, "status": "unreachable", "reason": type(exc).__name__}

    if len(response.content) > MAX_PAGE_BYTES:
        return {"url": url, "status": "rejected", "reason": "page_too_large", "http_status": response.status_code}
    if response.status_code >= 400:
        return {"url": url, "status": "unreachable", "reason": f"http_{response.status_code}", "http_status": response.status_code}
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        return {"url": url, "status": "rejected", "reason": f"non_html_content_type:{content_type}"}

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True)[:500] if soup.title else None
    language_hint = soup.html.get("lang") if soup.html else None
    context_by_url: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        normalized_href = normalize_url(anchor.get("href", ""), base=current_url)
        if not normalized_href or normalized_href in context_by_url:
            continue
        parent = anchor.parent
        surrounding = parent.get_text(" ", strip=True) if parent else anchor.get_text(" ", strip=True)
        context_by_url[normalized_href] = " ".join(surrounding.split())[:300]

    text, raw_links, canonical = extract_text_and_links(html, current_url)
    if len(text) < 20:
        return {"url": url, "status": "unreachable", "reason": "empty_or_js_only", "http_status": response.status_code}

    internal_details: list[dict] = []
    external_details: list[dict] = []
    seen: set[str] = set()
    for link in raw_links:
        normalized = normalize_url(link["href"], base=current_url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        entry = {
            "text": link["text"][:200],
            "href": normalized,
            "surrounding_text": context_by_url.get(normalized, ""),
        }
        host = urlparse(normalized).hostname or ""
        if registrable_domain(host) in approved_domains:
            internal_details.append(entry)
        else:
            external_details.append(entry)

    all_links = internal_details + external_details
    stored_text = text
    if all_links:
        stored_text += "\n\n--- LINKS ---\n" + "\n".join(
            f"{entry['text'] or '(no link text)'} -> {entry['href']}" for entry in all_links
        )
    stored_text = add_line_locators(stored_text)

    return {
        "url": url,
        "final_url": current_url,
        "status": "fetched",
        "http_status": response.status_code,
        "title": title,
        "language_hint": language_hint,
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "content_bytes": len(response.content),
        "text": stored_text,
        "internal_links": [entry["href"] for entry in internal_details],
        "external_links": [entry["href"] for entry in external_details],
        "internal_link_details": internal_details,
        "external_link_details": external_details,
        "canonical_url": canonical,
        "content_hash": hashlib.sha256(stored_text.encode("utf-8")).hexdigest(),
    }


async def fetch_many(
    urls: list[str], approved_domains: set[str], concurrency: int = MAX_CONCURRENT_FETCHES,
) -> list[dict]:
    semaphore = asyncio.Semaphore(max(1, concurrency))
    async with _build_async_client() as client:
        async def bounded(url: str) -> dict:
            async with semaphore:
                return await fetch_one_async(url, approved_domains, client)

        return await asyncio.gather(*(bounded(url) for url in urls))


async def run_fetch(
    manifest_path: Path,
    pages_dir: Path,
    output_path: Path,
    requested_urls: list[str],
    concurrency: int = MAX_CONCURRENT_FETCHES,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approved_domains = set(manifest.get("approved_domains", []))
    pages_dir.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        index = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        index = {"pages": [], "failures": [], "next_source_id_index": manifest["next_source_id_index"]}

    existing_by_url = {normalize_url(p["url"]) or p["url"]: p for p in index["pages"]}
    existing_hashes = {p["content_hash"] for p in index["pages"]}
    seed_url_to_id = {s["url"]: s["id"] for s in manifest["sources"] if s["type"] == "seed_url"}
    raw_urls = requested_urls or [s["url"] for s in manifest["sources"] if s["type"] == "seed_url"]

    deduplicated: list[str] = []
    seen: set[str] = set()
    for url in raw_urls:
        normalized = normalize_url(url) or url
        if normalized in seen or normalized in existing_by_url:
            continue
        seen.add(normalized)
        deduplicated.append(url)

    over_budget = deduplicated[MAX_URLS_PER_INVOCATION:]
    urls_to_fetch = deduplicated[:MAX_URLS_PER_INVOCATION]
    for url in over_budget:
        index["failures"].append({"url": url, "status": "rejected", "reason": "invocation_page_budget_exceeded"})

    try:
        results = await asyncio.wait_for(
            fetch_many(urls_to_fetch, approved_domains, concurrency=concurrency),
            timeout=TOTAL_FETCH_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        results = [
            {"url": url, "status": "unreachable", "reason": "retrieval_stage_timeout"}
            for url in urls_to_fetch
        ]
    fetched_count = 0
    for url, result in zip(urls_to_fetch, results, strict=True):
        if result["status"] != "fetched":
            index["failures"].append({key: value for key, value in result.items() if key != "text"})
            continue
        if result["content_hash"] in existing_hashes:
            continue

        normalized = normalize_url(url) or url
        source_id = seed_url_to_id.get(url) or seed_url_to_id.get(normalized) or f"p{index['next_source_id_index']:03d}"
        if source_id not in seed_url_to_id.values():
            index["next_source_id_index"] += 1

        (pages_dir / f"{source_id}.txt").write_text(result["text"], encoding="utf-8")
        metadata = {
            "source_id": source_id,
            "url": url,
            "final_url": result["final_url"],
            "http_status": result["http_status"],
            "title": result["title"],
            "language_hint": result["language_hint"],
            "retrieved_at": result["retrieved_at"],
            "content_bytes": result["content_bytes"],
            "content_hash": result["content_hash"],
            "canonical_url": result["canonical_url"],
            "internal_links": result["internal_links"],
            "external_links": result["external_links"],
            "internal_link_details": result["internal_link_details"],
            "external_link_details": result["external_link_details"],
        }
        (pages_dir / f"{source_id}.meta.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        page_entry = {
            "id": source_id,
            "url": url,
            "final_url": result["final_url"],
            "http_status": result["http_status"],
            "title": result["title"],
            "language_hint": result["language_hint"],
            "retrieved_at": result["retrieved_at"],
            "content_bytes": result["content_bytes"],
            "content_hash": result["content_hash"],
            "canonical_url": result["canonical_url"],
        }
        index["pages"].append(page_entry)
        existing_by_url[normalized] = page_entry
        existing_hashes.add(result["content_hash"])
        fetched_count += 1

    output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "fetched": fetched_count,
        "failures": len(index["failures"]),
        "total_pages": len(index["pages"]),
        "total_content_bytes": sum(page.get("content_bytes", 0) for page in index["pages"]),
        "concurrency": max(1, concurrency),
        "budget_rejections": len(over_budget),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--pages-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--url", action="append", default=[], dest="urls")
    parser.add_argument("--concurrency", type=int, default=MAX_CONCURRENT_FETCHES)
    args = parser.parse_args()

    result = asyncio.run(run_fetch(
        Path(args.manifest), Path(args.pages_dir), Path(args.output), args.urls,
        concurrency=min(max(1, args.concurrency), MAX_CONCURRENT_FETCHES),
    ))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

