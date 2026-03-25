"""
excel_parser.py — In-memory Excel and CSV parsing for FitMate admin upload pipeline.

Supports:
  - .xlsx via openpyxl (no pandas dependency — keeps image small)
  - .csv via built-in csv module (handles BOM from Windows Excel CSV export)

Column mapping — Excel headers must match these names (case-insensitive, spaces trimmed):
  mandarin_name, pinyin_name, latin_name, indonesian_name, english_name,
  is_toxic, target_organ, toxicity_level, description, source_reference
"""

import io
import csv
import openpyxl

# Required fields — rows missing any of these are invalid
REQUIRED_COLUMNS = {"mandarin_name", "indonesian_name", "is_toxic", "source_reference"}

# Valid toxicity levels (from TCMIngredient schema)
VALID_TOXICITY_LEVELS = {"low", "moderate", "high", "unknown"}

# is_toxic coercion maps
TRUTHY_VALUES = {"true", "1", "yes", "ya", "benar"}
FALSY_VALUES = {"false", "0", "no", "tidak", "salah"}


def parse_file(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parse an Excel or CSV file from raw bytes.
    Returns a list of row dicts with lowercase normalized keys.
    """
    name_lower = filename.lower()
    if name_lower.endswith(".xlsx"):
        return _parse_xlsx(file_bytes)
    elif name_lower.endswith(".csv"):
        return _parse_csv(file_bytes)
    else:
        raise ValueError(
            f"Format file tidak didukung: '{filename}'. Gunakan .xlsx atau .csv"
        )


def _parse_xlsx(file_bytes: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheet = wb.active

    # Row 1 = headers
    headers = []
    for cell in sheet[1]:
        val = cell.value
        headers.append(str(val).strip().lower() if val is not None else "")

    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue  # skip blank rows
        row_dict = {}
        for col_idx, value in enumerate(row):
            if col_idx < len(headers) and headers[col_idx]:
                row_dict[headers[col_idx]] = value
        rows.append(row_dict)

    return rows


def _parse_csv(file_bytes: bytes) -> list[dict]:
    # utf-8-sig handles BOM bytes added by Windows Excel CSV export
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    stream = io.StringIO(text)
    reader = csv.DictReader(stream)

    rows = []
    for row in reader:
        normalized = {
            k.strip().lower(): v.strip() if isinstance(v, str) else v
            for k, v in row.items()
            if k
        }
        if any(v for v in normalized.values()):  # skip empty rows
            rows.append(normalized)

    return rows


def validate_row(row: dict, row_number: int) -> list[dict]:
    """
    Validate a single parsed row against the TCMIngredient schema rules.
    Returns a list of error dicts: [{"field": ..., "message": ...}]
    An empty list means the row is valid.
    """
    errors = []

    # mandarin_name — required, non-empty
    mandarin = row.get("mandarin_name")
    if not mandarin or str(mandarin).strip() == "":
        errors.append({"field": "mandarin_name", "message": "Nama Mandarin wajib diisi"})

    # indonesian_name — required
    indonesian = row.get("indonesian_name")
    if not indonesian or str(indonesian).strip() == "":
        errors.append({"field": "indonesian_name", "message": "Nama Indonesia wajib diisi"})

    # is_toxic — required, must be a true/false-like value
    is_toxic_raw = str(row.get("is_toxic", "")).strip().lower()
    if is_toxic_raw not in TRUTHY_VALUES and is_toxic_raw not in FALSY_VALUES:
        errors.append({
            "field": "is_toxic",
            "message": (
                f"Nilai is_toxic tidak valid: '{row.get('is_toxic')}'. "
                "Gunakan true/false atau 1/0"
            ),
        })

    # source_reference — required, non-placeholder
    source = str(row.get("source_reference", "")).strip().lower()
    if not source or source in ("", "unknown", "none", "-", "n/a"):
        errors.append({
            "field": "source_reference",
            "message": "Referensi sumber wajib diisi (contoh: SymMap ID atau nomor BPOM)",
        })

    # toxicity_level — optional, but if present must be a valid enum value
    toxicity_level = str(row.get("toxicity_level", "")).strip().lower()
    if toxicity_level and toxicity_level not in VALID_TOXICITY_LEVELS:
        errors.append({
            "field": "toxicity_level",
            "message": (
                f"Nilai toxicity_level tidak valid: '{toxicity_level}'. "
                "Gunakan: low, moderate, high, unknown"
            ),
        })

    return errors


def normalize_row(row: dict) -> dict:
    """
    Convert a validated row dict to the exact TCMIngredient field types.
    Call ONLY after validate_row() returns an empty error list.
    """
    is_toxic_raw = str(row.get("is_toxic", "false")).strip().lower()
    is_toxic = is_toxic_raw in TRUTHY_VALUES

    toxicity_level = str(row.get("toxicity_level", "unknown")).strip().lower()
    if toxicity_level not in VALID_TOXICITY_LEVELS:
        toxicity_level = "unknown"

    def _str_or_none(key: str) -> str | None:
        val = str(row.get(key, "")).strip()
        return val if val else None

    return {
        "mandarin_name": str(row.get("mandarin_name", "")).strip(),
        "pinyin_name": _str_or_none("pinyin_name"),
        "latin_name": _str_or_none("latin_name"),
        "indonesian_name": str(row.get("indonesian_name", "")).strip(),
        "english_name": _str_or_none("english_name"),
        "is_toxic": is_toxic,
        "target_organ": _str_or_none("target_organ"),
        "toxicity_level": toxicity_level,
        "description": _str_or_none("description"),
        "source_reference": str(row.get("source_reference", "")).strip(),
        "validated_by": "pharmacy_team",
    }


def validate_all_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Validate all rows. Returns (valid_normalized_rows, error_summaries).

    error_summaries shape: [{"row": int, "errors": [{"field": str, "message": str}]}]
    Row numbers are 1-indexed from data perspective (row 2 in Excel = data row 1 = index 1).
    """
    valid_rows = []
    error_summaries = []

    for i, row in enumerate(rows):
        row_errors = validate_row(row, i)
        if row_errors:
            error_summaries.append({
                "row": i + 2,  # +2: row 1 is headers in Excel
                "errors": row_errors,
            })
        else:
            valid_rows.append(normalize_row(row))

    return valid_rows, error_summaries
