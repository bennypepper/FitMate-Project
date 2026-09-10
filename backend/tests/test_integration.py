import asyncio
import httpx
from main import app
from database.mongo import get_db
from services.safety import match_ingredients

async def run_all_tests():
    print("--- 1. Testing Database & Fallback ---")
    db = get_db()
    col = db["tcm_ingredients"]
    doc_count = await col.count_documents({})
    print(f"Database ingredient count: {doc_count}")
    assert doc_count >= 100, f"Expected >= 100 ingredients, got {doc_count}"

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
        print("Root check: PASS")

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

    print("--- ALL INTEGRATION TESTS PASSED! ---")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
