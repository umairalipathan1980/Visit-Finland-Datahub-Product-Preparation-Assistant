import json
import subprocess
import sys
from pathlib import Path

from conftest import PACKAGE_DIR, SCHEMAS_DIR, SCRIPTS_DIR


def run_validator(workspace):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_source_manifest.py"),
         "--input", str(workspace / "input" / "request.json"),
         "--schema", str(SCHEMAS_DIR / "analysis-request.schema.json"),
         "--output", str(workspace / "work" / "source-manifest.json")],
        capture_output=True, text=True,
    )


def write_request(workspace, request: dict):
    (workspace / "input" / "request.json").write_text(json.dumps(request), encoding="utf-8")


def base_request(**overrides):
    req = {
        "contract_version": "v1",
        "product_type": "accommodation",
        "website_urls": ["https://example.com"],
    }
    req.update(overrides)
    return req


def test_missing_website_urls_is_rejected(workspace):
    req = base_request()
    del req["website_urls"]
    write_request(workspace, req)
    result = run_validator(workspace)
    assert result.returncode != 0
    assert not (workspace / "work" / "source-manifest.json").exists()


def test_unknown_property_is_rejected(workspace):
    write_request(workspace, base_request(company_name="Acme"))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_wrong_contract_version_is_rejected(workspace):
    write_request(workspace, base_request(contract_version="v2"))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_scope_confirmation_rejects_interactive(workspace):
    write_request(workspace, base_request(scope_confirmation="interactive"))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_scope_confirmation_accepts_auto_confirm_single(workspace):
    write_request(workspace, base_request(scope_confirmation="auto_confirm_single"))
    result = run_validator(workspace)
    assert result.returncode == 0


def test_private_ip_url_is_rejected(workspace):
    write_request(workspace, base_request(website_urls=["http://127.0.0.1/"]))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_localhost_url_is_rejected(workspace):
    write_request(workspace, base_request(website_urls=["http://localhost/"]))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_document_path_traversal_is_rejected(workspace):
    write_request(workspace, base_request(document_files=["../../etc/passwd"]))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_unsupported_document_extension_is_rejected(workspace):
    (workspace / "input" / "documents" / "notes.txt").write_text("hi", encoding="utf-8")
    write_request(workspace, base_request(document_files=["documents/notes.txt"]))
    result = run_validator(workspace)
    assert result.returncode != 0


def test_successful_manifest_assigns_stable_ids_and_domains(workspace):
    write_request(workspace, base_request(website_urls=["https://www.example.com/a", "https://example.com/b"]))
    result = run_validator(workspace)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((workspace / "work" / "source-manifest.json").read_text(encoding="utf-8"))
    assert [s["id"] for s in manifest["sources"]] == ["p001", "p002"]
    assert manifest["approved_domains"] == ["example.com"]
    assert manifest["next_source_id_index"] == 3


def test_document_files_with_documents_prefix_is_accepted(workspace):
    """Regression: request.json's document_files entries are relative to input/
    and already include the 'documents/' prefix (Section 5's own example is
    'documents/brochure.pdf'), so the script must not join it a second time
    against a documents/-rooted base."""
    (workspace / "input" / "documents" / "brochure.pdf").write_bytes(b"%PDF-1.4 fake but present")
    write_request(workspace, base_request(document_files=["documents/brochure.pdf"]))
    result = run_validator(workspace)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((workspace / "work" / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["documents"][0]["relative_path"] == "documents/brochure.pdf"
    assert Path(manifest["documents"][0]["path"]).is_file()
