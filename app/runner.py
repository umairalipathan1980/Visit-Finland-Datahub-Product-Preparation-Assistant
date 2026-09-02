"""Sole application runner: the typed-tool Accommodation workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.runner_optimized import run_optimized_analysis


async def run_analysis(
    workspace: Path,
    package_dir: Path,
    env_bundle: dict,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    """Run the production typed-tool workflow.

    Keeping this stable entry point avoids coupling the API and CLI to
    implementation filenames.
    """
    return await run_optimized_analysis(
        workspace,
        package_dir,
        env_bundle,
        on_event=on_event,
    )
