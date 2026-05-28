import pytest

from app.dependencies.pdf_validator import (
    MAX_PDF_SIZE_BYTES,
    check_pdf_magic,
    check_pdf_size,
)


def test_check_pdf_magic_valid():
    assert check_pdf_magic(b"%PDF-1.4 some content") is True


def test_check_pdf_magic_invalid_zip():
    assert check_pdf_magic(b"PK\x03\x04") is False


def test_check_pdf_magic_empty():
    assert check_pdf_magic(b"") is False


def test_check_pdf_magic_short_content():
    assert check_pdf_magic(b"%PDF") is False  # 4바이트, magic은 5바이트


def test_check_pdf_size_at_limit():
    assert check_pdf_size(MAX_PDF_SIZE_BYTES) is True


def test_check_pdf_size_over_limit():
    assert check_pdf_size(MAX_PDF_SIZE_BYTES + 1) is False


def test_check_pdf_size_zero():
    assert check_pdf_size(0) is True



from unittest.mock import AsyncMock  # noqa: E402

from fastapi import UploadFile  # noqa: E402



@pytest.mark.asyncio
async def test_validate_pdf_upload_valid_file():
    from app.dependencies.pdf_validator import validate_pdf_upload

    content = b"%PDF-1.4 test content"
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.read = AsyncMock(return_value=content)
    result = await validate_pdf_upload(mock_file)
    assert result == content


@pytest.mark.asyncio
async def test_validate_pdf_upload_oversized_raises_413():
    from fastapi import HTTPException

    from app.dependencies.pdf_validator import MAX_PDF_SIZE_BYTES, validate_pdf_upload


    mock_file = AsyncMock(spec=UploadFile)
    mock_file.read = AsyncMock(return_value=b"%PDF-" + b"x" * (MAX_PDF_SIZE_BYTES + 1))
    with pytest.raises(HTTPException) as exc_info:
        await validate_pdf_upload(mock_file)
    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_pdf_upload_invalid_magic_raises_400():
    from fastapi import HTTPException

    from app.dependencies.pdf_validator import validate_pdf_upload


    mock_file = AsyncMock(spec=UploadFile)
    mock_file.read = AsyncMock(return_value=b"NOT A PDF CONTENT")
    with pytest.raises(HTTPException) as exc_info:
        await validate_pdf_upload(mock_file)
    assert exc_info.value.status_code == 400
