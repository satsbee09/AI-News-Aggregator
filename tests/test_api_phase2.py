import asyncio
import httpx
from app.server import app
from app.api.database import connect_to_mongo, close_mongo_connection, get_users_collection

async def run_test():
    print("1. Connecting to MongoDB...")
    await connect_to_mongo()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = "test_user_dashboard@example.com"
        
        # Cleanup any previous test data
        users_col = get_users_collection()
        await users_col.delete_one({"email": test_email})

        print("\n2. Testing POST /api/users (Upsert User)...")
        res = await client.post("/api/users", json={"email": test_email})
        print(f"   Status: {res.status_code}, User: {res.json()['email']}")
        assert res.status_code == 200
        assert res.json()["email"] == test_email
        assert len(res.json()["topics"]) > 0

        print("\n3. Testing PUT /api/users/{email}/topics (Update Topics)...")
        new_topics = [
            {"name": "Frontier AI & LLMs", "scope": "ai", "category": "ai"},
            {"name": "Ghaziabad Local News", "scope": "local", "category": "local"},
            {"name": "Quantum Computing", "scope": "general", "category": "general"},
            {"name": "Delhi NCR Weather", "scope": "weather", "category": "weather"}
        ]
        res = await client.put(f"/api/users/{test_email}/topics", json={"topics": new_topics})
        print(f"   Status: {res.status_code}, Topics count: {len(res.json()['topics'])}")
        assert res.status_code == 200
        assert len(res.json()["topics"]) == 4

        print("\n4. Testing GET /api/users/{email} (Retrieve User Profile)...")
        res = await client.get(f"/api/users/{test_email}")
        print(f"   Status: {res.status_code}, Retrieved Email: {res.json()['email']}")
        assert res.status_code == 200
        assert res.json()["email"] == test_email
        assert len(res.json()["topics"]) == 4

        print("\n5. Testing validation (Empty topics rejection)...")
        bad_res = await client.put(f"/api/users/{test_email}/topics", json={"topics": []})
        print(f"   Status: {bad_res.status_code} (Expected 422)")
        assert bad_res.status_code == 422

    await close_mongo_connection()
    print("\n[SUCCESS] Phase 2 User & Topic APIs test passed completely!")

if __name__ == "__main__":
    asyncio.run(run_test())
