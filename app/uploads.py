"""Bounded, streaming handling for API document uploads."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_SUFFIXES = {".pdf", ".docx"}
MAX_DOCUMENTS = 10
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_TOTAL_UPLOAD_BYTES = 50 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024


async def store_uploads(documents: list[UploadFile], destination: Path) -> list[Path]:
    named = [document for document in documents if document.filename]
    if len(named) > MAX_DOCUMENTS:
        raise HTTPException(status_code=413, detail=f"at most {MAX_DOCUMENTS} documents are allowed")

    stored: list[Path] = []
    seen_names: set[str] = set()
    total_bytes = 0
    for document in named:
        name = Path(document.filename or "").name
        if Path(name).suffix.lower() not in ALLOWED_SUFFIXES:
            raise HTTPException(status_code=400, detail=f"unsupported document type: {name}")
        if name.lower() in seen_names:
            raise HTTPException(status_code=400, detail=f"duplicate document filename: {name}")
        seen_names.add(name.lower())

        path = destination / name
        document_bytes = 0
        with path.open("wb") as output:
            while chunk := await document.read(UPLOAD_CHUNK_BYTES):
                document_bytes += len(chunk)
                total_bytes += len(chunk)
                if document_bytes > MAX_DOCUMENT_BYTES:
                    raise HTTPException(status_code=413, detail=f"document exceeds {MAX_DOCUMENT_BYTES} bytes: {name}")
                if total_bytes > MAX_TOTAL_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"uploads exceed {MAX_TOTAL_UPLOAD_BYTES} bytes in total")
                output.write(chunk)
        stored.append(path)
    return stored

