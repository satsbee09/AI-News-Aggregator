import asyncio
import httpx
from app.server import app
from app.config import settings

async def run_test():
    print("1. Testing FastAPI Internal Auth Protection...")
    transport = httpx.ASGITransport(app=app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"topics": [{"name": "Frontier AI & LLMs", "scope": "ai", "category": "ai"}]}
        
        # Test 1: Missing Secret Header
        print("\n2. Calling /internal/news-preview without X-Internal-Secret header...")
        res1 = await client.post("/internal/news-preview", json=payload)
        print(f"   Status Code: {res1.status_code} (Expected 401)")
        assert res1.status_code == 401, f"Expected 401 but got {res1.status_code}"
        print("   [SUCCESS] Correctly blocked unauthorized request!")

        # Test 2: Invalid Secret Header
        print("\n3. Calling /internal/news-preview with INVALID secret...")
        res2 = await client.post("/internal/news-preview", json=payload, headers={"X-Internal-Secret": "wrong_secret_123"})
        print(f"   Status Code: {res2.status_code} (Expected 401)")
        assert res2.status_code == 401, f"Expected 401 but got {res2.status_code}"
        print("   [SUCCESS] Correctly rejected invalid secret!")

        # Test 3: Valid Secret Header
        print("\n4. Calling /internal/news-preview with VALID X-Internal-Secret...")
        res3 = await client.post("/internal/news-preview", json=payload, headers={"X-Internal-Secret": settings.INTERNAL_API_SECRET})
        print(f"   Status Code: {res3.status_code} (Expected 200)")
        assert res3.status_code == 200, f"Expected 200 but got {res3.status_code}"
        assert "topics" in res3.json()
        print(f"   [SUCCESS] Authorized request processed! Topics count: {len(res3.json()['topics'])}")

    print("\n[SUCCESS] FastAPI Internal Route Security & Header Auth Verified!")

if __name__ == "__main__":
    asyncio.run(run_test())
