"""
upload_validation.py — Streaming upload size enforcement and image magic-byte checks.
"""

from fastapi import HTTPException, UploadFile, status

DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
CHUNK_SIZE = 64 * 1024  # 64 KB


async def read_upload_limited(
    file: UploadFile,
    max_bytes: int = DEFAULT_MAX_BYTES,
    detail: str = "File terlalu besar. Maksimum ukuran file adalah 10MB.",
) -> bytes:
    """
    Read an UploadFile in 64 KB chunks and raise HTTP 413 immediately
    if total bytes exceed max_bytes, preventing unbounded memory allocation.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=detail,
            )
        chunks.append(chunk)
    return b"".join(chunks)


def detect_image_mime(content: bytes) -> str | None:
    """
    Inspect magic bytes to verify content is a supported image format
    (JPEG, PNG, GIF, or WEBP). Returns MIME string or None if unrecognized.
    """
    if len(content) < 12:
        return None
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None
