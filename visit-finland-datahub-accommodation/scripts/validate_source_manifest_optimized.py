#!/usr/bin/env python3
"""PSL-aware entrypoint preserving validate_source_manifest.py's contract."""
from __future__ import annotations

import sys

import validate_source_manifest as base_validator
from domain_utils import registrable_domain


def main() -> int:
    base_validator.registrable_domain = registrable_domain
    return base_validator.main()


if __name__ == "__main__":
    sys.exit(main())
