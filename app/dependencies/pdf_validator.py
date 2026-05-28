from fastapi import HTTPException, UploadFile

MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
_PDF_MAGIC = b"%PDF-"


def check_pdf_magic(content: bytes) -> bool:
    return content[:5] == _PDF_MAGIC


def check_pdf_size(size: int) -> bool:
    return size <= MAX_PDF_SIZE_BYTES


async def validate_pdf_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if not check_pdf_size(len(content)):
        raise HTTPException(status_code=413, detail="파일 크기가 50MB를 초과합니다.")
    if not check_pdf_magic(content):
        raise HTTPException(status_code=400, detail="PDF 검증 실패: 잘못된 파일 형식")
    return content
