# Phase 1 Research: Data Foundation

## Validation Architecture

- **Automated validation**: Pydantic schema validation during MongoDB seeding — reject records missing mandarin_name, is_toxic flag, or target_organ
- **Expert-in-the-loop**: Excel-based workflow for pharmacists to review translations, add is_toxic flags, write medical_advice per ingredient before import
- **Traceability**: Every ingredient record must carry a source reference (SymMap ID or BPOM registration number) to ensure zero hallucination — no record enters without a traceable medical source
- **Test approach**: Unit tests for scraper output parsing, integration test for MongoDB seed script, manual review of sample ingredient records by pharmacy team

## TCMID & SymMap Data Sources

**SymMap v2.0** is the primary recommended source:
- Integrates TCMID, TCMSP, and HIT databases (comprehensive coverage)
- Updated against the 2020 Chinese Pharmacopoeia
- Offers **bulk Excel downloads** via Download page: Herbs (SMHB), Ingredients (SMIT), Herb-Ingredient mappings (SMHG), Target data
- This means BeautifulSoup scraping of TCMID page-by-page is NOT needed — bulk import via Pandas is cleaner and faster
- Access: http://www.symmap.org/download

**TCMID** (tcmid.org):
- Tables available but less structured than SymMap v2.0
- Some data accessible via table scraping but SymMap bulk download is preferred

## BPOM Data Source

Two separate BPOM systems are useful:

1. **standar-otskk.pom.go.id** ("Daftar Nama Bahan Obat Bahan Alam"):
   - Static tables of approved natural medicine ingredients with Indonesian common names
   - Excellent for mapping Mandarin/Latin names → official Indonesian names
   - Scrapable with BeautifulSoup4 + Requests
   - This is the key source for legitimizing Indonesian names

2. **cekbpom.pom.go.id**:
   - Product-level database — useful for verifying which TCM products are sold in Indonesia
   - Requires Selenium (dynamically loaded search results)
   - Rate-limited: implement 5-second throttle between requests
   - Use to build top-50 Indonesian TCM product list

## Scraping Strategy

| Source | Tool | Rationale |
|--------|------|-----------|
| SymMap bulk data | Pandas (direct download) | Structured Excel, no scraping needed |
| BPOM OTSKK (ingredient list) | BeautifulSoup4 + Requests | Static HTML tables |
| BPOM CekBPOM (product search) | Selenium + ChromeDriver | Dynamic JS-rendered results |

**Rate limiting**: 1–5 second delays between BPOM requests. Use `time.sleep()` with jitter. Use rotating user agents for BPOM CekBPOM.

**Anti-scraping**: BPOM has rate limits but no CAPTCHA on ingredient lists. CekBPOM may occasionally rate-limit — implement retry with exponential backoff.

## MongoDB Schema Design

### Collection: `tcm_ingredients`
```json
{
  "_id": ObjectId,
  "mandarin_name": "String (required)",
  "pinyin_name": "String",
  "latin_name": "String",
  "indonesian_name": "String (required)",
  "english_name": "String",
  "is_toxic": "Boolean (required)",
  "target_organ": "String (e.g., 'liver', 'heart', 'kidney')",
  "toxicity_level": "String (enum: 'low', 'moderate', 'high', 'unknown')",
  "description": "String",
  "symmap_id": "String (source traceability)",
  "bpom_reference": "String",
  "created_at": "DateTime",
  "validated_by": "String (pharmacist ID)"
}
```

### Collection: `safety_rules`
```json
{
  "_id": ObjectId,
  "ingredient_id": "ObjectId (FK → tcm_ingredients)",
  "condition_logic": "String (e.g., 'pregnancy', 'hypertension', 'concurrent_warfarin')",
  "warning_message": "String (Indonesian, shown to user)",
  "medical_advice": "String (rule-based response for WhatsApp bot)",
  "severity": "String (enum: 'warning', 'danger', 'contraindicated')",
  "source_reference": "String"
}
```

### Collection: `scan_logs`
```json
{
  "_id": ObjectId,
  "ocr_raw_text": "String",
  "detected_ingredients": ["String"],
  "warning_triggered": "Boolean",
  "scanned_at": "DateTime"
}
```

Use `pymongo` with `motor` (async) for FastAPI integration.

## Excel Validation Workflow

**Recommended Excel columns for pharmacist review:**

| Column | Type | Notes |
|--------|------|-------|
| mandarin_name | Text | From SymMap/BPOM, locked |
| pinyin_name | Text | From SymMap, editable |
| indonesian_name | Text | **Pharmacist fills/verifies** |
| is_toxic | Dropdown (TRUE/FALSE) | **Pharmacist decides** |
| target_organ | Dropdown (liver/heart/kidney/lung/other) | **Pharmacist selects** |
| toxicity_level | Dropdown (low/moderate/high/unknown) | **Pharmacist selects** |
| warning_message_id | Text | Warning message in Indonesian |
| medical_advice | Text | Rule-based chatbot response |
| source_reference | Text | SymMap ID or BPOM number |
| validated | Checkbox | Pharmacist marks when done |

Use `openpyxl` to generate the Excel with dropdowns, and Pandas for reading back validated data.

## Known Pitfalls

1. **Naming conflicts**: Same herb has 3-5 different Indonesian common names. Always anchor on Latin taxonomical name as the canonical identifier.
2. **BPOM rate limits**: CekBPOM will block aggressive scraping. Use 5s minimum delays.
3. **SymMap download size**: Full SymMap ingredient dataset is large — filter to herbs approved in Chinese Pharmacopoeia only for prototype.
4. **Mandarin encoding**: Always use UTF-8 throughout pipeline; Windows may default to GBK for Excel — specify `encoding='utf-8-sig'` in Pandas.
5. **Toxicity nuance**: "Toxic at high doses" ≠ "toxic at therapeutic doses" — pharmacist review is essential; never auto-flag based on scraping alone.
6. **MongoDB _id vs UUID**: Use MongoDB's native ObjectId for internal operations, but expose UUID strings to the API for consistency.

## Recommended Approach

**Priority order for prototype:**

1. Download SymMap v2.0 bulk Excel files (immediate, no scraping needed)
2. Filter to ~200 most common herbs used in Indonesian market
3. Generate pharmacist review Excel using `openpyxl`
4. Scrape BPOM OTSKK for official Indonesian name mappings (BeautifulSoup4)
5. After pharmacist validation, seed MongoDB using the validated Excel
6. Use BPOM CekBPOM (Selenium) only if time permits — not critical for prototype

**Plan structure:**
- Plan 01-01: Scraping & data collection pipeline (SymMap download + BPOM scraping + Excel export)
- Plan 01-02: MongoDB schema setup + seed script (collections, indexes, validation, seed from Excel)
