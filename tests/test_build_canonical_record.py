import json
import subprocess
import sys

from conftest import SCRIPTS_DIR


def run_build(workspace):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "build_canonical_record.py"),
         "--input", str(workspace / "work" / "staging-output" / "result.json"),
         "--output", str(workspace / "work" / "staging-output" / "canonical-product.json")],
        capture_output=True, text=True,
    )


def test_only_found_values_are_included(workspace):
    (workspace / "work" / "staging-output").mkdir(parents=True)
    result = {
        "run_metadata": {"schema_name": "poc-accommodation-schema-v1", "schema_version": "x",
                          "category_taxonomy_version": "x", "generated_at": "2026-01-01T00:00:00Z"},
        "product_type": "accommodation",
        "fields": {
            "name": {"fi": {"status": "found", "value": "Esimerkkihotelli"}, "en": {"status": "missing"}},
            "address": {"status": "review", "value": {"city": "Helsinki"}},
            "capacity": {"status": "found", "value": {"rooms": 42}},
            "availability": {"status": "found", "value": {"open_year_round": True}},
            "images": {"status": "not_in_scope"},
        },
    }
    (workspace / "work" / "staging-output" / "result.json").write_text(json.dumps(result), encoding="utf-8")

    rc = run_build(workspace)
    assert rc.returncode == 0, rc.stderr
    canonical = json.loads((workspace / "work" / "staging-output" / "canonical-product.json").read_text(encoding="utf-8"))
    assert canonical["fields"]["name"] == {"fi": "Esimerkkihotelli"}
    assert "address" not in canonical["fields"]  # status review, excluded
    assert canonical["fields"]["capacity"] == {"rooms": 42}
    assert canonical["fields"]["availability"] == {"open_year_round": True}
    assert "images" not in canonical["fields"]
