"""Request workspace creation (plan Section 5)."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


def build_request_workspace(base_dir: Path, website_urls: list[str], document_paths: list[Path],
                              languages: list[str] | None = None,
                              product_type: str = "accommodation") -> Path:
    run_id = uuid.uuid4().hex[:12]
    workspace = base_dir / run_id
    (workspace / "input" / "documents").mkdir(parents=True, exist_ok=True)
    (workspace / "work" / "pages").mkdir(parents=True, exist_ok=True)
    # work/staging-output/ is created by the agent when it writes its first
    # artifact there; the runner never creates output/ itself (Section 5).

    document_files = []
    for src in document_paths:
        dest_name = src.name
        dest = workspace / "input" / "documents" / dest_name
        shutil.copy2(src, dest)
        document_files.append(f"documents/{dest_name}")

    request = {
        "contract_version": "v1",
        "product_type": product_type,
        "website_urls": website_urls,
        "document_files": document_files,
        "languages": languages or ["fi", "en"],
        "scope_confirmation": "auto_confirm_single",
    }
    (workspace / "input" / "request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    return workspace
