from fastapi import HTTPException, status


def validate_pdf(file_bytes: bytes, filename: str, max_size_mb: int) -> None:
    """
    Validate that the uploaded file is a legitimate PDF within size limits.
    Raises HTTPException on validation failure.
    """
    # 1. Size check
    max_bytes = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {max_size_mb} MB",
        )

    # 2. Extension check
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted",
        )

    # 3. Magic bytes check — PDF files begin with %PDF
    if len(file_bytes) < 4 or file_bytes[:4] != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File does not appear to be a valid PDF",
        )
