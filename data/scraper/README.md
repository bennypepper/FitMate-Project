# FitMate TCM Scraper Pipeline

This directory contains the data foundation pipeline for FitMate. It downloads, scrapes, and formats TCM data for pharmacist validation.

## Workflow

1. Run `tcm_scraper.py` → downloads SymMap Excel to `output/symmap_raw.xlsx`
2. Run `bpom_scraper.py` → scrapes BPOM OTSKK to `output/bpom_ingredients.json`
3. Run `export_excel.py` → merges and exports to `output/tcm_for_validation.xlsx`
4. Pharmacy team reviews the file and saves it to `validated/tcm_validated.xlsx`

Ensure `pip install -r requirements.txt` is run before executing scripts.
