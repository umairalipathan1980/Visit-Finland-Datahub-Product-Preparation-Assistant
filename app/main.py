#!/usr/bin/env python3
"""CLI entrypoint for the Visit Finland DataHub Accommodation PoC runner."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.env_loader import EnvironmentError_, load_foundry_env
from app.preflight import run_preflight
from app.runner import run_analysis
from app.workspace import build_request_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "visit-finland-datahub-accommodation"
DEFAULT_WORKSPACE_BASE = REPO_ROOT / "runs"
DEFAULT_ENV_FILE = REPO_ROOT / ".env"


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the Accommodation Skill against a real request.")
    ap.add_argument("--website-url", action="append", default=[], dest="website_urls")
    ap.add_argument("--document", action="append", default=[], dest="documents")
    ap.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    ap.add_argument("--model", default=None)
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--workspace-base", default=str(DEFAULT_WORKSPACE_BASE))
    return ap


async def main_async() -> int:
    args = build_arg_parser().parse_args()

    try:
        env_bundle = load_foundry_env(Path(args.env_file), args.model)
    except EnvironmentError_ as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 64

    if args.preflight:
        result = await run_preflight(env_bundle, PACKAGE_DIR)
        print(json.dumps(result, indent=2))
        return 0 if result["ready"] else 70

    if not args.website_urls:
        print(json.dumps({"error": "at least one --website-url is required"}), file=sys.stderr)
        return 64

    workspace_base = Path(args.workspace_base)
    workspace_base.mkdir(parents=True, exist_ok=True)
    workspace = build_request_workspace(
        workspace_base, args.website_urls, [Path(d) for d in args.documents]
    )
    print(json.dumps({"workspace": str(workspace)}))

    outcome = await run_analysis(workspace, PACKAGE_DIR, env_bundle)
    print(json.dumps({"workspace": str(workspace), **outcome}, indent=2))

    from app.finalize import EXIT_CODES
    return EXIT_CODES[outcome["status"]]


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
