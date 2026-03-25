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

BPOM_OTSKK_URL = "https://standar-otskk.pom.go.id/index.php?tabel=daftar_bahan_alam"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

MAX_PAGES = 20  # Limit for prototype


def scrape_bpom_page(url: str, page: int = 1) -> list[dict]:
    """Scrape a single page of BPOM ingredient table."""
    params = {"page": page}
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        ingredients = []
        # Try common table structures on BPOM pages
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header
                cols = row.find_all("td")
                if len(cols) >= 2:
                    ingredient = {
                        "latin_name": cols[0].get_text(strip=True) if len(cols) > 0 else "",
                        "indonesian_name": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                        "mandarin_name": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                        "bpom_reference": f"BPOM-OTSKK-p{page}",
                    }
                    if ingredient["latin_name"]:
                        ingredients.append(ingredient)

        return ingredients
    except Exception as e:
        print(f"  [error] Page {page}: {e}")
        return []


def main():
    print("=== FitMate BPOM Scraper: OTSKK Ingredient List ===\n")
    all_ingredients = []

    for page in range(1, MAX_PAGES + 1):
        print(f"  [scraping] Page {page}/{MAX_PAGES}...")
        ingredients = scrape_bpom_page(BPOM_OTSKK_URL, page)

        if not ingredients:
            print(f"  [done] No more data at page {page}, stopping")
            break

        all_ingredients.extend(ingredients)
        print(f"  [ok] Found {len(ingredients)} ingredients on page {page}")

        # Polite rate limiting: 3-7 seconds between requests (BPOM rate limits)
        delay = random.uniform(3, 7)
        time.sleep(delay)

    output_path = OUTPUT_DIR / "bpom_ingredients.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_ingredients, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done. Scraped {len(all_ingredients)} BPOM ingredients → {output_path.name} ===")
    print("Next: run export_excel.py to generate pharmacist review file")


if __name__ == "__main__":
    main()
