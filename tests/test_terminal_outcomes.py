import json

import pytest

from app.finalize import classify_and_finalize


def valid_result_json():
    return {
        "run_metadata": {"schema_name": "poc-accommodation-schema-v1", "schema_version": "x",
                          "category_taxonomy_version": "x", "generated_at": "2026-01-01T00:00:00Z"},
        "product_type": "accommodation",
        "fields": {},
        "validation": {"valid": True, "errors": [], "warnings": []},
    }


def stage_success_artifacts(workspace):
    staging = workspace / "work" / "staging-output"
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "result.json").write_text(json.dumps(valid_result_json()), encoding="utf-8")
    (staging / "canonical-product.json").write_text("{}", encoding="utf-8")
    (staging / "result.xlsx").write_bytes(b"PK\x03\x04fake-xlsx-bytes")
    (staging / "review-report.md").write_text("# report", encoding="utf-8")


def test_completed_run_is_promoted_atomically(workspace):
    assert not (workspace / "output").exists()
    stage_success_artifacts(workspace)

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome["status"] == "completed"
    assert not (workspace / "work" / "staging-output").exists()
    output = workspace / "output"
    assert (output / "result.json").is_file()
    assert (output / "canonical-product.json").is_file()
    assert (output / "result.xlsx").is_file()
    assert (output / "review-report.md").is_file()
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert manifest["error_code"] is None
    assert set(manifest["artifact_hashes"]) == {
        "result.json", "canonical-product.json", "result.xlsx", "review-report.md",
    }
    assert all(len(value) == 64 for value in manifest["artifact_hashes"].values())


def test_completed_run_preserves_ambiguous_scope_as_review_metadata(workspace):
    stage_success_artifacts(workspace)
    scope_decision = {
        "status": "scope_ambiguous",
        "error_code": "product_boundary_unclear",
        "reason": "The product boundary remains uncertain.",
        "product": None,
        "excluded": [],
        "additional_products": [],
        "out_of_type_facilities": [],
    }
    (workspace / "work" / "scope-decision.json").write_text(json.dumps(scope_decision), encoding="utf-8")

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome == {"status": "completed", "error_code": None}
    output = workspace / "output"
    assert json.loads((output / "scope-decision.json").read_text(encoding="utf-8")) == scope_decision
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["scope_review_required"] is True
    assert manifest["scope_decision"] == scope_decision
    assert "scope-decision.json" in manifest["artifact_hashes"]


def test_runner_never_pre_creates_output(workspace):
    """output/ must be absent mid-run; only promotion creates it."""
    (workspace / "work" / "extraction-draft.json").write_text("{}", encoding="utf-8")
    assert not (workspace / "output").exists()


def test_export_failure_after_result_json_leaves_output_absent(workspace):
    staging = workspace / "work" / "staging-output"
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "result.json").write_text(json.dumps(valid_result_json()), encoding="utf-8")
    # export_xlsx.py crashed: no result.xlsx, no canonical-product.json, no review-report.md

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection",
                                       forced_status="execution_failed", forced_error_code="export_error")

    assert outcome["status"] == "execution_failed"
    assert not (workspace / "output").exists() or not (workspace / "output" / "result.json").is_file()
    assert (workspace / "work" / "staging-output" / "result.json").is_file()  # left intact for diagnostics


def test_scope_ambiguous_writes_scope_decision_and_no_product(workspace):
    scope_decision = {"status": "scope_ambiguous", "error_code": "multiple_accommodation_products"}
    (workspace / "work" / "scope-decision.json").write_text(json.dumps(scope_decision), encoding="utf-8")

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome == {"status": "scope_ambiguous", "error_code": "multiple_accommodation_products"}
    output = workspace / "output"
    assert (output / "scope-decision.json").is_file()
    assert not (output / "result.json").exists()
    assert (output / "review-report.md").is_file()
    assert (output / "run-manifest.json").is_file()


def test_no_usable_sources_when_nothing_retrieved(workspace):
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({"pages": [], "failures": []}), encoding="utf-8")

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome["status"] == "no_usable_sources"
    assert (workspace / "output" / "review-report.md").is_file()
    assert (workspace / "output" / "run-manifest.json").is_file()


def test_no_usable_sources_distinguishes_ocr_required(workspace):
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({"pages": [], "failures": []}), encoding="utf-8")
    (workspace / "work" / "parsed-documents.json").write_text(
        json.dumps({"documents": [{"id": "d001", "status": "parsed", "ocr_required": True}]}), encoding="utf-8")

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome == {"status": "no_usable_sources", "error_code": "documents_require_ocr"}


def test_validation_failed_retains_draft_and_diagnostics(workspace):
    staging = workspace / "work" / "staging-output"
    staging.mkdir(parents=True, exist_ok=True)
    invalid_result = valid_result_json()
    invalid_result["validation"] = {"valid": False, "errors": [{"rule_id": "schema_violation"}], "warnings": []}
    (staging / "result.json").write_text(json.dumps(invalid_result), encoding="utf-8")

    outcome = classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert outcome["status"] == "validation_failed"
    output = workspace / "output"
    assert (output / "extraction-draft.json").is_file()
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["validation_diagnostics"]["valid"] is False


@pytest.mark.parametrize("error_code", ["agent_timeout", "turn_limit_exceeded", "model_error", "fetcher_error", "export_error", "internal_error"])
def test_execution_failed_subcodes_are_reachable(workspace, error_code):
    outcome = classify_and_finalize(workspace, denials=[], verification_method=None,
                                       forced_status="execution_failed", forced_error_code=error_code)
    assert outcome == {"status": "execution_failed", "error_code": error_code}
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "execution_failed"


@pytest.mark.parametrize(("status", "error_code"), [
    ("cancelled", "run_cancelled"),
    ("interrupted", "backend_restarted"),
])
def test_lifecycle_terminal_statuses_are_persisted(workspace, status, error_code):
    outcome = classify_and_finalize(
        workspace, [], None, forced_status=status, forced_error_code=error_code,
        stage_reached="stage_3",
    )
    assert outcome == {"status": status, "error_code": error_code}
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == status


def test_unhandled_exception_path_still_produces_report_and_manifest(workspace):
    """Simulates the runner's `finally` block after an exception mid-run."""
    outcome = classify_and_finalize(workspace, denials=[], verification_method=None,
                                       forced_status="execution_failed", forced_error_code="internal_error",
                                       stage_reached="stage_3")
    output = workspace / "output"
    assert (output / "review-report.md").is_file()
    assert (output / "run-manifest.json").is_file()


def test_full_report_is_not_overwritten_by_minimal_one(workspace):
    scope_decision = {"status": "scope_ambiguous", "error_code": "product_boundary_unclear"}
    (workspace / "work" / "scope-decision.json").write_text(json.dumps(scope_decision), encoding="utf-8")
    (workspace / "work" / "staging-output").mkdir(parents=True, exist_ok=True)
    full_report = "# Full agent-written report\nDetailed content here."
    (workspace / "work" / "staging-output" / "review-report.md").write_text(full_report, encoding="utf-8")

    classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    promoted = (workspace / "output" / "review-report.md").read_text(encoding="utf-8")
    assert promoted == full_report


def test_denied_tool_calls_are_recorded_in_manifest(workspace):
    denials = [{"command": "bash scripts/x.py", "reason": "Only the pinned interpreter may be invoked."}]
    classify_and_finalize(workspace, denials=denials, verification_method="transcript_inspection")
    manifest = json.loads((workspace / "output" / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["denied_tool_calls"] == denials


def test_promotion_refuses_to_overwrite_existing_output(workspace):
    (workspace / "output").mkdir(parents=True)
    stage_success_artifacts(workspace)
    with pytest.raises(RuntimeError):
        classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")


def test_completed_run_prunes_work_directory(workspace):
    (workspace / "work" / "pages" / "p001.txt").write_text("evidence text", encoding="utf-8")
    (workspace / "input" / "documents" / "brochure.pdf").parent.mkdir(parents=True, exist_ok=True)
    (workspace / "input" / "documents" / "brochure.pdf").write_bytes(b"%PDF-fake")
    stage_success_artifacts(workspace)

    classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert not (workspace / "work").exists()
    assert not (workspace / "input" / "documents").exists()
    assert (workspace / "output" / "result.json").is_file()  # promoted artifacts untouched


def test_no_usable_sources_prunes_work_directory(workspace):
    (workspace / "work" / "fetched-pages.json").write_text(json.dumps({"pages": [], "failures": []}), encoding="utf-8")

    classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert not (workspace / "work").exists()


def test_validation_failed_keeps_work_directory_for_debugging(workspace):
    staging = workspace / "work" / "staging-output"
    staging.mkdir(parents=True, exist_ok=True)
    invalid_result = valid_result_json()
    invalid_result["validation"] = {"valid": False, "errors": [{"rule_id": "schema_violation"}], "warnings": []}
    (staging / "result.json").write_text(json.dumps(invalid_result), encoding="utf-8")
    (workspace / "work" / "pages").mkdir(parents=True, exist_ok=True)
    (workspace / "work" / "pages" / "p001.txt").write_text("evidence text", encoding="utf-8")

    classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert (workspace / "work" / "pages" / "p001.txt").is_file()


def test_execution_failed_keeps_work_directory_for_debugging(workspace):
    (workspace / "work" / "pages").mkdir(parents=True, exist_ok=True)
    (workspace / "work" / "pages" / "p001.txt").write_text("evidence text", encoding="utf-8")

    classify_and_finalize(workspace, denials=[], verification_method=None,
                           forced_status="execution_failed", forced_error_code="fetcher_error")

    assert (workspace / "work" / "pages" / "p001.txt").is_file()


def test_scope_ambiguous_keeps_work_directory(workspace):
    scope_decision = {"status": "scope_ambiguous", "error_code": "multiple_accommodation_products"}
    (workspace / "work" / "scope-decision.json").write_text(json.dumps(scope_decision), encoding="utf-8")
    (workspace / "work" / "pages").mkdir(parents=True, exist_ok=True)
    (workspace / "work" / "pages" / "p001.txt").write_text("evidence text", encoding="utf-8")

    classify_and_finalize(workspace, denials=[], verification_method="transcript_inspection")

    assert (workspace / "work" / "pages" / "p001.txt").is_file()
