"""
test_admin_upload.py — Tests for Excel/CSV upload pipeline (Plan 05-03).

Requirements covered: DATA-03
"""

import io
import pytest
import openpyxl
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Test Helpers ────────────────────────────────────────────────────────────

VALID_HEADERS = [
    "mandarin_name",
    "pinyin_name",
    "latin_name",
    "indonesian_name",
    "english_name",
    "is_toxic",
    "target_organ",
    "toxicity_level",
    "description",
    "source_reference",
]

VALID_ROW = {
    "mandarin_name": "附子",
    "pinyin_name": "Fu Zi",
    "latin_name": "Aconitum carmichaelii",
    "indonesian_name": "Akar Monkshood",
    "english_name": "Prepared Aconite Root",
    "is_toxic": "true",
    "target_organ": "jantung",
    "toxicity_level": "high",
    "description": "Bahan toksik dengan efek kardiotoksik.",
    "source_reference": "SymMap-SMIT00001",
}


def make_xlsx_bytes(rows: list[dict], headers: list[str] | None = None) -> bytes:
    """Helper: create an in-memory .xlsx file with given rows."""
    wb = openpyxl.Workbook()
    ws = wb.active

    if not headers:
        headers = list(rows[0].keys()) if rows else []

    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ─── Unit Tests: excel_parser ────────────────────────────────────────────────

def test_parse_xlsx_returns_correct_rows():
    """parse_file can parse a valid .xlsx file and return expected row count."""
    from utils.excel_parser import parse_file

    xlsx_bytes = make_xlsx_bytes([VALID_ROW], VALID_HEADERS)
    rows = parse_file(xlsx_bytes, "test.xlsx")

    assert len(rows) == 1
    assert rows[0]["mandarin_name"] == "附子"


def test_validate_row_valid():
    """validate_row returns empty error list for a fully valid row."""
    from utils.excel_parser import validate_row

    errors = validate_row(VALID_ROW, 2)
    assert errors == []


def test_validate_row_missing_mandarin_name():
    """validate_row flags missing/empty mandarin_name."""
    from utils.excel_parser import validate_row

    row = {**VALID_ROW, "mandarin_name": ""}
    errors = validate_row(row, 2)
    assert any(e["field"] == "mandarin_name" for e in errors)


def test_validate_row_invalid_is_toxic():
    """validate_row flags non-boolean is_toxic values."""
    from utils.excel_parser import validate_row

    row = {**VALID_ROW, "is_toxic": "maybe"}
    errors = validate_row(row, 2)
    assert any(e["field"] == "is_toxic" for e in errors)


def test_validate_row_placeholder_source_reference():
    """validate_row flags 'unknown' as an invalid source_reference."""
    from utils.excel_parser import validate_row

    row = {**VALID_ROW, "source_reference": "unknown"}
    errors = validate_row(row, 2)
    assert any(e["field"] == "source_reference" for e in errors)


def test_normalize_row_converts_is_toxic_to_bool():
    """normalize_row correctly converts is_toxic string to Python bool."""
    from utils.excel_parser import normalize_row

    true_row = normalize_row({**VALID_ROW, "is_toxic": "true"})
    assert true_row["is_toxic"] is True

    false_row = normalize_row({**VALID_ROW, "is_toxic": "false"})
    assert false_row["is_toxic"] is False


def test_normalize_row_ya_is_truthy():
    """normalize_row recognises Indonesian 'ya' as True."""
    from utils.excel_parser import normalize_row

    row = normalize_row({**VALID_ROW, "is_toxic": "ya"})
    assert row["is_toxic"] is True


# ─── Integration Tests: upload endpoints ─────────────────────────────────────

def test_validate_endpoint_with_valid_file(client, auth_headers):
    """DATA-03: /validate returns valid_count > 0 and empty errors for a good file."""
    xlsx_bytes = make_xlsx_bytes([VALID_ROW], VALID_HEADERS)
    response = client.post(
        "/api/v1/admin/upload/validate",
        headers={k: v for k, v in auth_headers.items() if k != "Content-Type"},
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid_count"] == 1
    assert data["error_count"] == 0
    assert data["errors"] == []


def test_validate_endpoint_catches_invalid_rows(client, auth_headers):
    """DATA-03: /validate returns error_count > 0 and row errors for bad rows."""
    bad_row = {**VALID_ROW, "mandarin_name": "", "source_reference": "unknown"}
    xlsx_bytes = make_xlsx_bytes([bad_row], VALID_HEADERS)
    response = client.post(
        "/api/v1/admin/upload/validate",
        headers={k: v for k, v in auth_headers.items() if k != "Content-Type"},
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error_count"] > 0
    assert len(data["errors"]) > 0
    assert data["errors"][0]["row"] == 2  # Excel row 2 = first data row


def test_validate_endpoint_requires_auth(client):
    """AUTH-02: /validate without Authorization header returns 403."""
    xlsx_bytes = make_xlsx_bytes([VALID_ROW], VALID_HEADERS)
    response = client.post(
        "/api/v1/admin/upload/validate",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code in (401, 403)


def test_import_endpoint_upserts_to_mongodb(client, auth_headers):
    """DATA-03: /import successfully upserts rows and returns imported count."""
    xlsx_bytes = make_xlsx_bytes([VALID_ROW], VALID_HEADERS)

    mock_result = MagicMock()
    mock_result.upserted_id = "new_id_abc123"

    with patch("routers.upload.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.tcm_ingredients.update_one = AsyncMock(return_value=mock_result)
        mock_get_db.return_value = mock_db

        response = client.post(
            "/api/v1/admin/upload/import",
            headers={k: v for k, v in auth_headers.items() if k != "Content-Type"},
            files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["imported"] == 1
    assert data["updated"] == 0
