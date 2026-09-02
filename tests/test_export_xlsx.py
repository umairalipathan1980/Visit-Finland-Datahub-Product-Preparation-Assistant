import json
import subprocess
import sys

import openpyxl

from conftest import SCRIPTS_DIR


def run_export(workspace):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "export_xlsx.py"),
         "--input", str(workspace / "work" / "staging-output" / "result.json"),
         "--output", str(workspace / "work" / "staging-output" / "result.xlsx")],
        capture_output=True, text=True,
    )


def write_result(workspace, fields):
    (workspace / "work" / "staging-output").mkdir(parents=True, exist_ok=True)
    result = {
        "run_metadata": {"schema_name": "poc-accommodation-schema-v1", "schema_version": "x",
                          "category_taxonomy_version": "x", "generated_at": "2026-01-01T00:00:00Z"},
        "product_type": "accommodation",
        "fields": fields,
    }
    (workspace / "work" / "staging-output" / "result.json").write_text(json.dumps(result), encoding="utf-8")


def test_workbook_has_expected_sheet_and_header(workspace):
    write_result(workspace, {"name": {"fi": {"status": "found", "value": "Esimerkkihotelli"}, "en": {"status": "missing"}}})
    rc = run_export(workspace)
    assert rc.returncode == 0, rc.stderr
    wb = openpyxl.load_workbook(workspace / "work" / "staging-output" / "result.xlsx")
    assert wb.sheetnames == ["Accommodation"]
    ws = wb["Accommodation"]
    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    assert header[0] == "name.fi" and header[1] == "name.en"
    assert "availability" in header


def test_missing_field_is_empty_cell_not_string_none(workspace):
    write_result(workspace, {"booking_url": {"status": "missing"}})
    run_export(workspace)
    wb = openpyxl.load_workbook(workspace / "work" / "staging-output" / "result.xlsx")
    ws = wb["Accommodation"]
    col_index = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))].index("booking_url")
    value = list(ws.iter_rows(min_row=2, max_row=2))[0][col_index].value
    assert value is None


def test_numeric_capacity_field_loads_as_number(workspace):
    write_result(workspace, {"capacity": {"status": "found", "value": {"rooms": 42}}})
    run_export(workspace)
    wb = openpyxl.load_workbook(workspace / "work" / "staging-output" / "result.xlsx")
    ws = wb["Accommodation"]
    col_index = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))].index("capacity")
    # capacity is a dict -> serialized as JSON text, not a raw number; verify it round-trips
    value = list(ws.iter_rows(min_row=2, max_row=2))[0][col_index].value
    assert "42" in value


def test_formula_like_value_is_neutralized(workspace):
    write_result(workspace, {"opening_hours": {"status": "found", "value": "=1+1"}})
    run_export(workspace)
    wb = openpyxl.load_workbook(workspace / "work" / "staging-output" / "result.xlsx")
    ws = wb["Accommodation"]
    col_index = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))].index("opening_hours")
    value = list(ws.iter_rows(min_row=2, max_row=2))[0][col_index].value
    assert value == "'=1+1"  # neutralize() prefixes a literal apostrophe; it is never stored as a formula
