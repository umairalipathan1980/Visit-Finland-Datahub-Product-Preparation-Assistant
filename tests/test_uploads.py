import io

import pytest
from fastapi import HTTPException, UploadFile

import app.uploads as uploads


@pytest.mark.asyncio
async def test_store_uploads_streams_allowed_file(tmp_path):
    upload = UploadFile(filename="brochure.pdf", file=io.BytesIO(b"pdf-content"))
    paths = await uploads.store_uploads([upload], tmp_path)
    assert paths == [tmp_path / "brochure.pdf"]
    assert paths[0].read_bytes() == b"pdf-content"


@pytest.mark.asyncio
async def test_store_uploads_rejects_unsupported_type(tmp_path):
    upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"text"))
    with pytest.raises(HTTPException) as exc:
        await uploads.store_uploads([upload], tmp_path)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_store_uploads_enforces_per_document_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_DOCUMENT_BYTES", 3)
    upload = UploadFile(filename="large.pdf", file=io.BytesIO(b"four"))
    with pytest.raises(HTTPException) as exc:
        await uploads.store_uploads([upload], tmp_path)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_store_uploads_enforces_document_count(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_DOCUMENTS", 1)
    files = [
        UploadFile(filename="one.pdf", file=io.BytesIO(b"one")),
        UploadFile(filename="two.pdf", file=io.BytesIO(b"two")),
    ]
    with pytest.raises(HTTPException) as exc:
        await uploads.store_uploads(files, tmp_path)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_store_uploads_enforces_total_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_DOCUMENT_BYTES", 10)
    monkeypatch.setattr(uploads, "MAX_TOTAL_UPLOAD_BYTES", 5)
    files = [
        UploadFile(filename="one.pdf", file=io.BytesIO(b"one")),
        UploadFile(filename="two.pdf", file=io.BytesIO(b"two")),
    ]
    with pytest.raises(HTTPException) as exc:
        await uploads.store_uploads(files, tmp_path)
    assert exc.value.status_code == 413
