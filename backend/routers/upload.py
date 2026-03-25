"""
upload.py — Admin Excel/CSV upload router.

Two-phase upload pipeline:
  POST /api/v1/admin/upload/validate — Dry-run: parse + validate, no DB writes
  POST /api/v1/admin/upload/import   — Live import: validate + upsert to MongoDB

Both endpoints require valid admin JWT (Depends(get_current_admin)).
Max file size: 10MB.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from utils.auth import get_current_admin
from utils.excel_parser import parse_file, validate_all_rows
from database.mongo import get_db

router = APIRouter(prefix="/api/v1/admin/upload", tags=["admin-upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
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


@router.post("/validate")
async def validate_upload(
    file: UploadFile = File(...),
    admin: str = Depends(get_current_admin),
):
    """
    Dry-run validation.
    Parses the uploaded file and validates all rows WITHOUT writing to MongoDB.
    Returns a structured summary with row-level error details.
    """
    _check_extension(file)

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File terlalu besar. Maksimum ukuran file adalah 10MB.",
        )

    try:
        rows = parse_file(file_bytes, file.filename or "upload.xlsx")
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
async def import_upload(
    file: UploadFile = File(...),
    admin: str = Depends(get_current_admin),
):
    """
    Confirmed import.
    Validates the uploaded file and upserts all valid rows to MongoDB
    using mandarin_name as the natural key. Invalid rows are skipped.
    """
    _check_extension(file)

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File terlalu besar. Maksimum ukuran file adalah 10MB.",
        )

    try:
        rows = parse_file(file_bytes, file.filename or "upload.xlsx")
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

    for row_data in valid_rows:
        try:
            result = await db.tcm_ingredients.update_one(
                {"mandarin_name": row_data["mandarin_name"]},  # natural key
                {"$set": row_data},
                upsert=True,
            )
            if result.upserted_id:
                imported_count += 1  # new document inserted
            else:
                updated_count += 1  # existing document updated
        except Exception:
            failed_count += 1  # individual row failure — continue processing

    total_processed = imported_count + updated_count + failed_count
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
        "skipped_invalid": len(error_summaries),
        "message": message,
    }
