"""Terminal-outcome classification, minimal failure report, and atomic promotion.

Implements the terminal contract: every run ends in exactly one recognized
statuses, `output/` is either absent or complete, and a report plus manifest
exist for every outcome except `input_invalid`.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path

EXIT_CODES = {
    "completed": 0,
    "scope_ambiguous": 2,
    "no_usable_sources": 3,
    "validation_failed": 4,
    "execution_failed": 70,
    "input_invalid": 64,
    "cancelled": 130,
    "interrupted": 70,
}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _read_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _minimal_report(workspace: Path, status: str, error_code: str | None, stage_reached: str) -> str:
    request = _read_json(workspace / "input" / "request.json") or {}
    fetched = _read_json(workspace / "work" / "fetched-pages.json") or {}
    parsed = _read_json(workspace / "work" / "parsed-documents.json") or {}

    lines = [
        f"# Run report ({status})",
        "",
        f"- status: `{status}`",
        f"- error_code: `{error_code}`",
        f"- stage reached: {stage_reached}",
        f"- website_urls requested: {request.get('website_urls', [])}",
        f"- pages retrieved: {len(fetched.get('pages', []))}",
        f"- retrieval failures: {len(fetched.get('failures', []))}",
        f"- documents parsed: {sum(1 for d in parsed.get('documents', []) if d.get('status') == 'parsed')}",
        f"- documents requiring OCR: {sum(1 for d in parsed.get('documents', []) if d.get('ocr_required'))}",
        "",
        "This is a minimal deterministic report assembled by the runner from workspace state, "
        "not the model's own review report, because the run did not reach Stage 7.",
    ]
    return "\n".join(lines)


def _write_manifest_and_report(target_dir: Path, status: str, error_code: str | None, workspace: Path,
                                 stage_reached: str, denials: list, verification_method: str | None,
                                 extra: dict | None = None) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    report_path = target_dir / "review-report.md"
    if not report_path.is_file():
        report_path.write_text(_minimal_report(workspace, status, error_code, stage_reached), encoding="utf-8")

    manifest = {
        "status": status,
        "error_code": error_code,
        "exit_code": EXIT_CODES[status],
        "stage_reached": stage_reached,
        "finalized_at": _now(),
        "skill_verification_method": verification_method,
        "denied_tool_calls": denials,
    }
    if extra:
        manifest.update(extra)
    (target_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


_PRUNABLE_STATUSES = {"completed", "no_usable_sources"}


def _prune_workspace(workspace: Path, status: str) -> None:
    """Store only what's required, for the library view -- but only for the
    two statuses where nothing under work/ has further value:

    - `completed`: every evidence excerpt a 'found'/'review' field cites is
      already embedded verbatim in output/result.json, so the raw scraped
      page text and parsed document segments serve no further purpose.
    - `no_usable_sources`: there was nothing retrieved to begin with.

    Every other status keeps work/ intact on purpose: `validation_failed`
    and `execution_failed` are exactly the outcomes a developer needs
    workspace state to debug (the plan's own "the draft is kept deliberately"
    rule), and `scope_ambiguous` keeps the already-fetched pages available
    for a possible future resume-after-selection flow.
    """
    if status not in _PRUNABLE_STATUSES:
        return
    work_dir = workspace / "work"
    if work_dir.is_dir():
        shutil.rmtree(work_dir, ignore_errors=True)
    documents_dir = workspace / "input" / "documents"
    if documents_dir.is_dir():
        shutil.rmtree(documents_dir, ignore_errors=True)


def classify_and_finalize(workspace: Path, denials: list, verification_method: str | None,
                            forced_status: str | None = None, forced_error_code: str | None = None,
                            stage_reached: str = "unknown") -> dict:
    """Inspect workspace state and produce the terminal outcome.

    `forced_status` is set by the caller when an exception or timeout already
    determined the outcome (execution_failed and its sub-codes); otherwise
    this function derives the outcome from files on disk exactly as a
    completely independent finalizer would have to.
    """
    output_dir = workspace / "output"
    staging_dir = workspace / "work" / "staging-output"

    def promote_partial_report() -> None:
        """A partial `review-report.md` may already sit in staging even though the
        run stopped before Stage 7 completed -- surface it instead of the minimal
        fallback, matching the 'full report is not overwritten' rule."""
        staged_report = staging_dir / "review-report.md"
        if staged_report.is_file() and not (output_dir / "review-report.md").is_file():
            output_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_report, output_dir / "review-report.md")

    if forced_status:
        promote_partial_report()
        _write_manifest_and_report(output_dir, forced_status, forced_error_code, workspace, stage_reached,
                                     denials, verification_method)
        _prune_workspace(workspace, forced_status)
        return {"status": forced_status, "error_code": forced_error_code}

    result = _read_json(staging_dir / "result.json")
    scope_decision = _read_json(workspace / "work" / "scope-decision.json")
    fetched = _read_json(workspace / "work" / "fetched-pages.json") or {}
    parsed = _read_json(workspace / "work" / "parsed-documents.json") or {}

    staged_complete = (
        result is not None
        and (staging_dir / "canonical-product.json").is_file()
        and (staging_dir / "result.xlsx").is_file()
        and (staging_dir / "review-report.md").is_file()
    )

    # Checked in reverse pipeline order: evidence of a later stage having run
    # (a staged result.json, a scope decision) takes priority over evidence
    # that would only matter if the run never got that far.
    if staged_complete and result.get("validation", {}).get("valid") is True:
        scope_review_required = bool(scope_decision and scope_decision.get("status") == "scope_ambiguous")
        if scope_review_required and not (staging_dir / "scope-decision.json").is_file():
            shutil.copy2(workspace / "work" / "scope-decision.json", staging_dir / "scope-decision.json")
        artifact_names = ["result.json", "canonical-product.json", "result.xlsx", "review-report.md"]
        if (staging_dir / "scope-decision.json").is_file():
            artifact_names.append("scope-decision.json")
        artifact_hashes = {
            name: hashlib.sha256((staging_dir / name).read_bytes()).hexdigest()
            for name in artifact_names
        }
        manifest_extra = {"artifact_hashes": artifact_hashes}
        if scope_review_required:
            manifest_extra.update({"scope_review_required": True, "scope_decision": scope_decision})
        _write_manifest_and_report(
            staging_dir, "completed", None, workspace, "stage_7", denials, verification_method,
            extra=manifest_extra,
        )
        if output_dir.exists():
            raise RuntimeError("output/ already exists; refusing to overwrite a prior run's promoted artifacts")
        os.rename(staging_dir, output_dir)
        _prune_workspace(workspace, "completed")
        return {"status": "completed", "error_code": None}

    if result is not None and result.get("validation", {}).get("valid") is False:
        promote_partial_report()
        _write_manifest_and_report(output_dir, "validation_failed", "schema_or_rule_violation", workspace,
                                     "stage_6", denials, verification_method,
                                     extra={"validation_diagnostics": result.get("validation")})
        shutil.copy2(staging_dir / "result.json", output_dir / "extraction-draft.json")
        _prune_workspace(workspace, "validation_failed")
        return {"status": "validation_failed", "error_code": "schema_or_rule_violation"}

    if scope_decision and scope_decision.get("status") == "scope_ambiguous":
        promote_partial_report()
        error_code = scope_decision.get("error_code", "product_boundary_unclear")
        _write_manifest_and_report(output_dir, "scope_ambiguous", error_code, workspace, "stage_4", denials,
                                     verification_method, extra={"scope_decision": scope_decision})
        shutil.copy2(workspace / "work" / "scope-decision.json", output_dir / "scope-decision.json")
        return {"status": "scope_ambiguous", "error_code": error_code}

    pages_ok = len(fetched.get("pages", [])) > 0
    docs_ok = any(d.get("status") == "parsed" and not d.get("ocr_required") for d in parsed.get("documents", []))
    if not pages_ok and not docs_ok:
        promote_partial_report()
        docs_attempted = len(parsed.get("documents", [])) > 0
        error_code = "documents_require_ocr" if (docs_attempted and not docs_ok and not pages_ok) else "all_pages_inaccessible"
        _write_manifest_and_report(output_dir, "no_usable_sources", error_code, workspace, "stage_3", denials,
                                     verification_method)
        _prune_workspace(workspace, "no_usable_sources")
        return {"status": "no_usable_sources", "error_code": error_code}

    promote_partial_report()
    _write_manifest_and_report(output_dir, "execution_failed", "internal_error", workspace, stage_reached,
                                 denials, verification_method)
    _prune_workspace(workspace, "execution_failed")
    return {"status": "execution_failed", "error_code": "internal_error"}
