import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "visit-finland-datahub-accommodation"
SCRIPTS_DIR = PACKAGE_DIR / "scripts"
SCHEMAS_DIR = PACKAGE_DIR / "schemas"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "ws"
    (ws / "input" / "documents").mkdir(parents=True)
    (ws / "work" / "pages").mkdir(parents=True)
    return ws
