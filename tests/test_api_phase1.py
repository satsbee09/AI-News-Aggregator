import asyncio
import httpx
from app.server import app
from app.api.database import connect_to_mongo, close_mongo_connection

async def run_test():
    print("1. Testing MongoDB connection via Motor...")
    await connect_to_mongo()

    print("\n2. Testing GET /api/health endpoint via AsyncClient...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        print(f"   Status code: {response.status_code}")
        print(f"   Response JSON: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["mongodb"] == "connected"

    await close_mongo_connection()
    print("\n[SUCCESS] Phase 1 FastAPI & Motor MongoDB connection test passed completely!")

if __name__ == "__main__":
    asyncio.run(run_test())
