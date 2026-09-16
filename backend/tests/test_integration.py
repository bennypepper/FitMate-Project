import asyncio
import httpx
from main import app
from database.mongo import get_db
from database.ingredient_repository import ingredient_repository
from services.safety import match_ingredients

async def run_all_tests():
    print("--- 1. Testing Database & Fallback ---")
    db = get_db()
    col = db["tcm_ingredients"]
    count = await col.count_documents({})
    assert count >= 100
    print(f"Database ingredient count: {count}")

    print("--- 2. Testing Multilingual Safety Matching ---")
    test_queries = [
        ("Ren Shen", "ginseng", False),
        ("Ginkgo Biloba", "ginkgo biloba", True),
        ("Fu Zi", "aconite", True),
        ("Licorice", "licorice", False),
        ("Zhu Sha", "cinnabar", True),
        ("Guan Mu Tong", "aristolochia", True),
        ("Luo Han Guo", "monk fruit", False)
    ]
    for raw_name, expected_name, should_be_toxic in test_queries:
        matched = await match_ingredients([raw_name], db)
        if should_be_toxic:
            assert len(matched["toxic"]) > 0, f"Expected toxic match for {raw_name}, got {matched}"
            item = matched["toxic"][0]
            print(f"Query: {raw_name:<15} -> Matched TOXIC: {item.get('english_name') or item.get('indonesian_name')}")
        else:
            assert len(matched["safe"]) > 0, f"Expected safe match for {raw_name}, got {matched}"
            item = matched["safe"][0]
            print(f"Query: {raw_name:<15} -> Matched SAFE:  {item.get('english_name') or item.get('indonesian_name')}")

    # Test non-herbal food snack text
    snack_res = await match_ingredients(["Naraya Rice Crackers", "Krekers Beras Rasa Asin"], db)
    assert snack_res["meta"]["is_herbal_product"] == False
    assert snack_res["meta"]["classification"] == "non_herbal"
    assert len(snack_res["toxic"]) == 0
    assert len(snack_res["safe"]) == 0
    assert len(snack_res["unknown"]) == 2
    print("Non-herbal food snack test: PASS (Correctly flagged non_herbal)")

    print("--- 3. Testing API Endpoints via ASGI ---")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Health
        res = await client.get("/health")
        assert res.status_code == 200 and res.json()["status"] == "healthy"
        print("Health check: PASS")

        # Root
        res = await client.get("/")
        assert res.status_code == 200
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-frame-options") == "DENY"
        assert "strict-origin-when-cross-origin" in res.headers.get("referrer-policy", "")
        assert "max-age=31536000" in res.headers.get("strict-transport-security", "")
        print("Root check & security headers: PASS")

        # Analyze endpoint with dummy file
        files = {"file": ("dummy.txt", b"dummy content", "text/plain")}
        res = await client.post("/api/v1/analyze/", files=files)
        print(f"Analyze invalid MIME: status {res.status_code}")
        assert res.status_code == 400

        # WhatsApp test-chat endpoint
        wa_payload = {"sender": "integration_test", "message": "Apakah Fu Zi aman?"}
        wa_res = await client.post("/api/v1/whatsapp/test-chat", json=wa_payload)
        print(f"WhatsApp test-chat: status {wa_res.status_code}")
        assert wa_res.status_code == 200
        assert wa_res.json()["status"] == "success"
        print("WhatsApp test-chat: PASS")

        # Bridge session endpoint
        bridge_res = await client.post("/api/v1/bridge/session")
        print(f"Bridge create session: status {bridge_res.status_code}")
        assert bridge_res.status_code == 200
        session_id = bridge_res.json()["session_id"]
        assert session_id.startswith("fm_")

        bridge_st = await client.get(f"/api/v1/bridge/{session_id}/status")
        assert bridge_st.status_code == 200
        assert bridge_st.json()["status"] == "waiting"
        print("Bridge session status check: PASS")

        # Analyze Search endpoint
        search_res = await client.get("/api/v1/analyze/search?q=ginseng&limit=5")
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert "items" in search_data
        assert len(search_data["items"]) > 0
        print(f"Analyze search check: PASS (Found {len(search_data['items'])} matches for 'ginseng')")

    print("--- 4. Testing Ingredient Repository & Admin Search ---")
    admin_items, admin_total, admin_pages = await ingredient_repository.admin_list(
        db, page=1, limit=10, search_query="ginseng"
    )
    assert admin_total > 0
    assert len(admin_items) <= 10
    print(f"Repository admin_list search: PASS (Found {admin_total} total matches across catalog)")

    fuzzy_doc, fuzzy_score = await ingredient_repository.fuzzy_lookup("ren shen", db)
    assert fuzzy_doc is not None
    assert fuzzy_score >= 80
    print(f"Repository fuzzy_lookup: PASS (Matched '{fuzzy_doc.get('indonesian_name')}' with score {fuzzy_score})")

    print("--- 5. Testing Proxy-Aware Client IP Extractor ---")
    from core.limiter import get_client_ip
    from starlette.requests import Request as StarletteRequest

    # Test CF-Connecting-IP
    scope_cf = {"type": "http", "headers": [(b"cf-connecting-ip", b"203.0.113.195")], "client": ("10.0.0.1", 12345)}
    req_cf = StarletteRequest(scope_cf)
    assert get_client_ip(req_cf) == "203.0.113.195"

    # Test X-Forwarded-For
    scope_xff = {"type": "http", "headers": [(b"x-forwarded-for", b"198.51.100.42, 10.0.0.2")], "client": ("10.0.0.1", 12345)}
    req_xff = StarletteRequest(scope_xff)
    assert get_client_ip(req_xff) == "198.51.100.42"

    # Test direct client host fallback
    scope_direct = {"type": "http", "headers": [], "client": ("192.0.2.1", 12345)}
    req_direct = StarletteRequest(scope_direct)
    assert get_client_ip(req_direct) == "192.0.2.1"
    print("Proxy-aware client IP extractor: PASS")

    print("--- ALL INTEGRATION TESTS PASSED! ---")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
