import importlib
import sys

from conftest import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))
domain_utils = importlib.import_module("domain_utils")


def test_registrable_domain_uses_public_suffix_list():
    assert domain_utils.registrable_domain("rooms.example.co.uk") == "example.co.uk"
    assert domain_utils.registrable_domain("www.example.fi") == "example.fi"

