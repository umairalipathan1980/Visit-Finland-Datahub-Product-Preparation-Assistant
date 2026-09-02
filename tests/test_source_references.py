import json

from app.agent_tools import _build_source_catalog, _cited_source_counts


def evidence(source_id: str, excerpt: str) -> dict:
    return {
        "source_id": source_id,
        "locator": "main content",
        "excerpt": excerpt,
        "quote_verified": True,
    }


def test_cited_source_counts_includes_localized_and_alternative_evidence():
    result = {
        "fields": {
            "name": {
                "fi": {"status": "found", "value": "Hotelli", "evidence": [evidence("p001", "Hotelli")]},
                "en": {"status": "missing"},
            },
            "description": {
                "status": "found",
                "value": "Description",
                "evidence": [evidence("p001", "Description")],
                "alternatives": [
                    {
                        "value": "Other",
                        "reason": "Conflicting brochure wording",
                        "evidence": [evidence("d001", "Other")],
                    }
                ],
            },
        }
    }

    assert _cited_source_counts(result) == {"p001": 2, "d001": 1}


def test_source_catalog_contains_only_cited_sanitized_metadata(workspace):
    pages_dir = workspace / "work" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (workspace / "work" / "fetched-pages.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "id": "p001",
                        "url": "https://example.fi/hotel?utm_source=ad&lang=fi#rooms",
                        "final_url": "https://example.fi/hotel?utm_source=ad&lang=fi#rooms",
                    },
                    {"id": "p999", "url": "https://example.fi/uncited"},
                ],
                "failures": [],
            }
        ),
        encoding="utf-8",
    )
    (pages_dir / "p001.meta.json").write_text(
        json.dumps({"title": "Example Hotel", "retrieved_at": "2026-09-02T10:00:00Z"}),
        encoding="utf-8",
    )
    (workspace / "work" / "parsed-documents.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "id": "d001",
                        "file_name": "brochure.pdf",
                        "relative_path": "brochure.pdf",
                        "path": "C:/private/upload/brochure.pdf",
                        "parsing_method": "pypdf",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = {
        "fields": {
            "name": {"status": "found", "evidence": [evidence("p001", "Example Hotel")]},
            "pricing": {"status": "found", "evidence": [evidence("d001", "From EUR 100")]},
        }
    }

    catalog = _build_source_catalog(workspace, result)
    by_id = {source["source_id"]: source for source in catalog["sources"]}

    assert set(by_id) == {"p001", "d001"}
    assert by_id["p001"] == {
        "source_id": "p001",
        "source_type": "website",
        "title": "Example Hotel",
        "url": "https://example.fi/hotel?lang=fi",
        "retrieved_at": "2026-09-02T10:00:00Z",
        "citation_count": 1,
    }
    assert by_id["d001"] == {
        "source_id": "d001",
        "source_type": "document",
        "file_name": "brochure.pdf",
        "parsing_method": "pypdf",
        "citation_count": 1,
    }
    assert "p999" not in by_id
    assert "private" not in json.dumps(catalog)