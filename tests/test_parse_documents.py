import json
import subprocess
import sys

from docx import Document
from reportlab.pdfgen import canvas

from conftest import SCRIPTS_DIR


def run_parser(workspace):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "parse_documents.py"),
         "--manifest", str(workspace / "work" / "source-manifest.json"),
         "--output", str(workspace / "work" / "parsed-documents.json")],
        capture_output=True, text=True,
    )


def write_manifest(workspace, documents):
    manifest = {
        "contract_version": "v1", "product_type": "accommodation",
        "sources": [], "approved_domains": [], "documents": documents,
        "next_source_id_index": 1,
    }
    (workspace / "work" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def make_pdf(path, pages_text):
    c = canvas.Canvas(str(path))
    for text in pages_text:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()


def make_empty_pdf(path):
    c = canvas.Canvas(str(path))
    c.showPage()
    c.save()


def make_docx(path, paragraphs):
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(str(path))


def test_multi_page_pdf_produces_page_locators(workspace):
    pdf_path = workspace / "input" / "documents" / "brochure.pdf"
    make_pdf(pdf_path, ["Esimerkkihotelli sijaitsee keskustassa", "42 huonetta ja sauna"])
    write_manifest(workspace, [{"id": "d001", "type": "document", "path": str(pdf_path), "relative_path": "brochure.pdf"}])

    result = run_parser(workspace)
    assert result.returncode == 0, result.stderr
    parsed = json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8"))
    doc = parsed["documents"][0]
    assert doc["status"] == "parsed"
    assert doc["ocr_required"] is False
    locators = [s["locator"] for s in doc["segments"]]
    assert locators == ["page 1", "page 2"]
    assert "Esimerkkihotelli" in doc["segments"][0]["text"]


def test_empty_pdf_is_flagged_ocr_required(workspace):
    pdf_path = workspace / "input" / "documents" / "scanned.pdf"
    make_empty_pdf(pdf_path)
    write_manifest(workspace, [{"id": "d001", "type": "document", "path": str(pdf_path), "relative_path": "scanned.pdf"}])

    result = run_parser(workspace)
    assert result.returncode == 0, result.stderr
    parsed = json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8"))
    assert parsed["documents"][0]["ocr_required"] is True


def test_docx_paragraphs_are_extracted(workspace):
    docx_path = workspace / "input" / "documents" / "details.docx"
    make_docx(docx_path, ["Osoite: Esimerkkitie 1", "Hinnat alkaen 90 euroa"])
    write_manifest(workspace, [{"id": "d001", "type": "document", "path": str(docx_path), "relative_path": "details.docx"}])

    result = run_parser(workspace)
    assert result.returncode == 0, result.stderr
    parsed = json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8"))
    doc = parsed["documents"][0]
    assert doc["status"] == "parsed"
    assert any("Esimerkkitie" in s["text"] for s in doc["segments"])


def test_legacy_doc_extension_is_rejected(workspace):
    fake_doc = workspace / "input" / "documents" / "old.doc"
    fake_doc.write_bytes(b"not a real doc file")
    write_manifest(workspace, [{"id": "d001", "type": "document", "path": str(fake_doc), "relative_path": "old.doc"}])

    result = run_parser(workspace)
    assert result.returncode == 0, result.stderr
    parsed = json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8"))
    assert parsed["documents"][0]["status"] == "rejected"


def test_corrupt_pdf_does_not_crash_and_is_not_reported_missing(workspace):
    corrupt_path = workspace / "input" / "documents" / "corrupt.pdf"
    corrupt_path.write_bytes(b"%PDF-1.4 not actually a valid pdf structure")
    write_manifest(workspace, [{"id": "d001", "type": "document", "path": str(corrupt_path), "relative_path": "corrupt.pdf"}])

    result = run_parser(workspace)
    assert result.returncode == 0, result.stderr
    parsed = json.loads((workspace / "work" / "parsed-documents.json").read_text(encoding="utf-8"))
    assert parsed["documents"][0]["status"] == "parse_failed"
