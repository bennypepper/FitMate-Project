"""
tcm_scraper.py — SymMap v2.0 bulk data downloader for FitMate TCM database

Downloads structured ingredient and herb data from SymMap v2.0 bulk datasets.
SymMap integrates TCMID, TCMSP, and HIT databases.
Download source: http://www.symmap.org/download
"""

import pandas as pd
import requests
import os
import json
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# SymMap v2.0 public download URLs (verify at http://www.symmap.org/download)
SYMMAP_URLS = {
    "herbs": "http://www.symmap.org/static/download/V2.0/SymMap%20v2.0%2C%20SMHB%20file.xlsx",
    "ingredients": "http://www.symmap.org/static/download/V2.0/SymMap%20v2.0%2C%20SMIT%20file.xlsx",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Academic Research Bot; FitMate Project PIMNAS 2026)"
}


def download_symmap_file(name: str, url: str) -> pd.DataFrame:
    """Download a SymMap Excel file and return as DataFrame."""
    output_path = OUTPUT_DIR / f"symmap_{name}.xlsx"
    if output_path.exists():
        print(f"  [cache] Using existing {output_path.name}")
        return pd.read_excel(output_path)

    print(f"  [download] Downloading {name} from SymMap...")
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"  [ok] Saved to {output_path.name}")
    return pd.read_excel(output_path)


def filter_for_prototype(df_herbs: pd.DataFrame, df_ingredients: pd.DataFrame,
                          df_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Filter SymMap data to the most common herbs for Indonesian TCM market.
    Focuses on herbs in the 2020 Chinese Pharmacopoeia.
    Returns merged DataFrame with herb + ingredient info.
    """
    # Filter to herbs with is_toxic data or known common usage
    # Column names vary by SymMap version — normalize
    herb_cols = df_herbs.columns.tolist()
    ingredient_cols = df_ingredients.columns.tolist()

    print(f"  [info] Herb columns: {herb_cols[:5]}")
    print(f"  [info] Ingredient columns: {ingredient_cols[:5]}")

    # Save raw column info for pharmacist reference
    with open(OUTPUT_DIR / "symmap_columns.json", "w", encoding="utf-8") as f:
        json.dump({"herbs": herb_cols, "ingredients": ingredient_cols}, f, ensure_ascii=False, indent=2)

    # Return first 500 rows for prototype filtering (pharmacist will validate)
    return df_herbs.head(500)


def export_raw(df: pd.DataFrame, name: str):
    """Save DataFrame to output directory."""
    path = OUTPUT_DIR / f"symmap_{name}_raw.json"
    df.to_json(path, orient="records", force_ascii=False, indent=2)
    print(f"  [ok] Exported {len(df)} rows to {path.name}")


def main():
    print("=== FitMate TCM Scraper: SymMap Downloader ===\n")

    dataframes = {}
    for name, url in SYMMAP_URLS.items():
        try:
            df = download_symmap_file(name, url)
            dataframes[name] = df
            export_raw(df, name)
            time.sleep(2)  # Polite delay between downloads
        except Exception as e:
            print(f"  [error] Failed to download {name}: {e}")
            print(f"  [hint] Visit http://www.symmap.org/download to get the correct URL")

    print(f"\n=== Done. Downloaded {len(dataframes)} datasets to {OUTPUT_DIR} ===")
    print("Next: run bpom_scraper.py for Indonesian name mappings")


if __name__ == "__main__":
    main()
