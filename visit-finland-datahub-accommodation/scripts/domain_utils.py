"""Public-Suffix-List-aware domain helpers for the optimized workflow."""
from __future__ import annotations

import tldextract

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())


def registrable_domain(host: str) -> str:
    result = _EXTRACT(host.lower().rstrip("."))
    if not result.suffix:
        return result.domain
    return f"{result.domain}.{result.suffix}" if result.domain else result.suffix

