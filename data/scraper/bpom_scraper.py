"""
bpom_scraper.py — BPOM OTSKK ingredient scraper for FitMate

Scrapes the official Indonesian BPOM approved ingredient list from:
standar-otskk.pom.go.id — Daftar Nama Bahan Obat Bahan Alam

This provides official Indonesian common names for TCM ingredients,
which is critical for the Mandarin → Indonesian translation layer.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BPOM_OTSKK_URL = "https://standar-otskk.pom.go.id/otskk-db/kategori/daftar-nama-bahan-obat-bahan-alam-dan-klaim-yang-disetujui"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

def scrape_bpom_page(url: str) -> list[dict]:
    """Scrape the BPOM ingredient table."""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        ingredients = []
        table = soup.find("table")
        if not table:
            return []
            
        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip header
            cols = row.find_all("td")
            # New format: cols[0]=Indonesian Name, cols[1]=Latin Name, cols[2]=Claims
            if len(cols) >= 2:
                ingredient = {
                    "indonesian_name": cols[0].get_text(strip=True),
                    "latin_name": cols[1].get_text(strip=True),
                    "mandarin_name": "", # BPOM doesn't list Mandarin names
                    "bpom_reference": "BPOM-OTSKK-Klaim",
                }
                if ingredient["latin_name"] and ingredient["indonesian_name"]:
                    ingredients.append(ingredient)

        return ingredients
    except Exception as e:
        print(f"  [error] Failed to scrape: {e}")
        return []


def main():
    print("=== FitMate BPOM Scraper: OTSKK Ingredient List ===\n")
    
    print("  [scraping] Fetching data...")
    all_ingredients = scrape_bpom_page(BPOM_OTSKK_URL)

    if not all_ingredients:
        print("  [error] No data found.")
    else:
        print(f"  [ok] Found {len(all_ingredients)} ingredients")

    output_path = OUTPUT_DIR / "bpom_ingredients.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_ingredients, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done. Scraped {len(all_ingredients)} BPOM ingredients → {output_path.name} ===")
    print("Next: run export_excel.py to generate pharmacist review file")


if __name__ == "__main__":
    main()
