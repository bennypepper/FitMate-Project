import re
import logging
from thefuzz import fuzz

logger = logging.getLogger("fitmate.repository")

class IngredientRepository:
    """
    Centralized repository and in-memory cache for TCM ingredients.
    Eliminates redundant database queries and unifies fuzzy/token lookups.
    """
    def __init__(self):
        self._cached_ingredients: list[dict] | None = None
        self._cached_lookup_keys: dict[str, dict] | None = None

    def invalidate_cache(self) -> None:
        """Invalidate the in-memory cache (e.g., after database mutations or uploads)."""
        logger.info("[Repository] In-memory ingredient cache invalidated.")
        self._cached_ingredients = None
        self._cached_lookup_keys = None

    async def get_all_ingredients(self, db) -> list[dict]:
        """Fetch all ingredients from cache or database."""
        if self._cached_ingredients is not None:
            return self._cached_ingredients

        logger.info("[Repository] Loading TCM ingredients into cache from database...")
        cursor = db["tcm_ingredients"].find({})
        ingredients = await cursor.to_list(length=3000)

        lookup_keys = {}
        for item in ingredients:
            for field in ["mandarin_name", "pinyin_name", "indonesian_name", "english_name", "latin_name"]:
                val = item.get(field)
                if val and isinstance(val, str):
                    cleaned = val.strip().lower()
                    if cleaned and cleaned not in ("-", "unknown", "none"):
                        lookup_keys[cleaned] = item

        self._cached_ingredients = ingredients
        self._cached_lookup_keys = lookup_keys
        logger.info(f"[Repository] Cached {len(ingredients)} ingredients with {len(lookup_keys)} lookup keys.")
        return self._cached_ingredients

    async def get_lookup_keys(self, db) -> dict[str, dict]:
        """Return the precomputed normalized name lookup dictionary."""
        if self._cached_lookup_keys is None:
            await self.get_all_ingredients(db)
        return self._cached_lookup_keys or {}

    async def search_ingredients(self, query: str, db, limit: int = 20) -> list[dict]:
        """Public search across all names with relevance scoring."""
        all_ingredients = await self.get_all_ingredients(db)
        clean_query = (query or "").strip().lower()

        if not clean_query:
            return all_ingredients[:limit]

        matches = []
        for ing in all_ingredients:
            names = [
                str(ing.get("indonesian_name") or "").lower(),
                str(ing.get("mandarin_name") or "").lower(),
                str(ing.get("pinyin_name") or "").lower(),
                str(ing.get("english_name") or "").lower(),
                str(ing.get("latin_name") or "").lower(),
            ]
            score = 0
            for n in names:
                if not n:
                    continue
                if clean_query == n:
                    score = max(score, 100)
                elif clean_query in n or n in clean_query:
                    score = max(score, 80)
            if score > 0:
                matches.append((score, ing))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]

    async def fuzzy_lookup(self, query: str, db) -> tuple[dict | None, int]:
        """
        Fuzzy match ingredient name against all variants.
        Returns (best_match_doc, score) or (None, 0).
        """
        all_ingredients = await self.get_all_ingredients(db)
        if not all_ingredients:
            return None, 0

        clean_query = query.strip().lower()
        lookup = await self.get_lookup_keys(db)

        # 1. Exact match check
        if clean_query in lookup:
            return lookup[clean_query], 100

        # 2. Fuzzy token set ratio matching
        best_match = None
        highest_score = 0

        for ing in all_ingredients:
            candidates = [
                ing.get("indonesian_name", ""),
                ing.get("mandarin_name", ""),
                ing.get("pinyin_name", "") or "",
                ing.get("english_name", "") or "",
                ing.get("latin_name", "") or "",
            ]
            score = max(
                fuzz.token_set_ratio(clean_query, str(c).lower())
                for c in candidates if str(c).strip()
            )
            if score > highest_score:
                highest_score = score
                best_match = ing

        return best_match, highest_score

    async def admin_list(
        self,
        db,
        page: int = 1,
        limit: int = 20,
        search_query: str = ""
    ) -> tuple[list[dict], int, int]:
        """
        Paginated ingredient listing for admin portal.
        Supports filtering across all 500 ingredients.
        Returns: (items, total_count, total_pages)
        """
        all_ingredients = await self.get_all_ingredients(db)
        q = search_query.strip().lower()

        if q:
            filtered = [
                ing for ing in all_ingredients
                if q in str(ing.get("mandarin_name") or "").lower()
                or q in str(ing.get("indonesian_name") or "").lower()
                or q in str(ing.get("latin_name") or "").lower()
                or q in str(ing.get("english_name") or "").lower()
                or q in str(ing.get("pinyin_name") or "").lower()
            ]
        else:
            filtered = all_ingredients

        # Sort by mandarin_name ascending
        sorted_items = sorted(filtered, key=lambda x: str(x.get("mandarin_name", "")))

        total = len(sorted_items)
        pages = max(1, (total + limit - 1) // limit)
        skip = (page - 1) * limit
        paginated = sorted_items[skip : skip + limit]

        cleaned = []
        for item in paginated:
            doc = dict(item)
            doc["_id"] = str(doc.get("_id", ""))
            cleaned.append(doc)

        return cleaned, total, pages

ingredient_repository = IngredientRepository()
