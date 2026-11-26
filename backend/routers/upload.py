"""
upload.py — Admin Excel/CSV upload router.

Two-phase upload pipeline:
  POST /api/v1/admin/upload/validate — Dry-run: parse + validate, no DB writes
  POST /api/v1/admin/upload/import   — Live import: validate + upsert to MongoDB

Both endpoints require valid admin JWT (Depends(get_current_admin)).
Max file size: 10MB.
"""

import asyncio
import logging
import os
from typing import Annotated

from core.limiter import limiter
from database.mongo import get_db
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from utils.auth import get_current_admin
from utils.excel_parser import parse_file, validate_all_rows
from utils.upload_validation import read_upload_limited

logger = logging.getLogger("fitmate.upload")

router = APIRouter(prefix="/api/v1/admin/upload", tags=["admin-upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".xlsx", ".csv"}

def _check_extension(file: UploadFile) -> None:
    """Validate uploaded file has an allowed extension."""
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Format file tidak didukung: '{ext}'. "
                "Gunakan .xlsx atau .csv"
            ),
        )


def build_upsert_filter(doc: dict) -> dict:
    """Build compound natural-key filter so non-Mandarin BPOM/FHI herbs don't collide."""
    mandarin = (doc.get("mandarin_name") or "").strip()
    if mandarin:
        return {"mandarin_name": mandarin}
    return {
        "indonesian_name": (doc.get("indonesian_name") or "").strip(),
        "latin_name": (doc.get("latin_name") or "").strip(),
    }

@router.post("/validate")
@limiter.limit("10/minute")
async def validate_upload(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    admin: str = Depends(get_current_admin),
):
    """
    Dry-run validation.
    Parses the uploaded file and validates all rows WITHOUT writing to MongoDB.
    Returns a structured summary with row-level error details.
    """
    _check_extension(file)

    file_bytes = await read_upload_limited(
        file,
        max_bytes=MAX_FILE_SIZE,
        detail="File terlalu besar. Maksimum ukuran file adalah 10MB.",
    )

    try:
        rows = await asyncio.to_thread(parse_file, file_bytes, file.filename or "upload.xlsx")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not rows:
        raise HTTPException(
            status_code=422,
            detail=(
                "File kosong atau tidak memiliki data. "
                "Pastikan baris pertama adalah header kolom."
            ),
        )

    valid_rows, error_summaries = validate_all_rows(rows)

    return {
        "total_rows": len(rows),
        "valid_count": len(valid_rows),
        "error_count": len(error_summaries),
        "errors": error_summaries,
        "filename": file.filename,
    }

@router.post("/import")
@limiter.limit("10/minute")
async def import_upload(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    admin: str = Depends(get_current_admin),
):
    """
    Confirmed import.
    Validates the uploaded file and upserts all valid rows to MongoDB
    using mandarin_name as the natural key. Invalid rows are skipped.
    """
    _check_extension(file)

    file_bytes = await read_upload_limited(
        file,
        max_bytes=MAX_FILE_SIZE,
        detail="File terlalu besar. Maksimum ukuran file adalah 10MB.",
    )

    try:
        rows = await asyncio.to_thread(parse_file, file_bytes, file.filename or "upload.xlsx")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    valid_rows, error_summaries = validate_all_rows(rows)

    if not valid_rows:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Tidak ada baris yang valid untuk diimpor. "
                f"{len(error_summaries)} baris bermasalah."
            ),
        )

    db = get_db()
    imported_count = 0
    updated_count = 0
    failed_count = 0

    failed_rows = []
    for row_data in valid_rows:
        try:
            upsert_filter = build_upsert_filter(row_data)
            result = await db.tcm_ingredients.update_one(
                upsert_filter,
                {"$set": row_data},
                upsert=True,
            )
            if result.upserted_id:
                imported_count += 1
            else:
                updated_count += 1
        except Exception:
            logger.exception(
                f"[Upload] Failed to upsert ingredient '{row_data.get('mandarin_name') or row_data.get('indonesian_name')}'",
            )
            failed_count += 1
            failed_rows.append({
                "mandarin_name": row_data.get("mandarin_name"),
                "indonesian_name": row_data.get("indonesian_name"),
                "reason": "Gagal menyimpan baris ke database",
            })

    if imported_count + updated_count > 0:
        from database.ingredient_repository import ingredient_repository
        ingredient_repository.invalidate_cache()

    message = (
        f"Impor selesai: {imported_count} bahan baru ditambahkan, "
        f"{updated_count} bahan diperbarui."
    )
    if failed_count:
        message += f" {failed_count} baris gagal disimpan."

    return {
        "success": True,
        "imported": imported_count,
        "updated": updated_count,
        "failed": failed_count,
        "failed_rows": failed_rows,
        "skipped_invalid": len(error_summaries),
        "message": message,
    }
