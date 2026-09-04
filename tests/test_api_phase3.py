import asyncio
import httpx
from app.server import app
from app.api.database import connect_to_mongo, close_mongo_connection

async def run_test():
    print("1. Connecting to MongoDB...")
    await connect_to_mongo()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n2. Testing POST /api/news/preview with multiple topics (AI, Weather, Local)...")
        topics_payload = [
            {"name": "Frontier AI & LLMs", "scope": "ai", "category": "ai"},
            {"name": "Delhi NCR Weather", "scope": "weather", "category": "weather"},
            {"name": "Ghaziabad news", "scope": "local", "category": "local"}
        ]
        
        res = await client.post("/api/news/preview", json={"topics": topics_payload})
        print(f"   Status code: {res.status_code}")
        assert res.status_code == 200
        
        data = res.json()
        assert "topics" in data
        print(f"   Received {len(data['topics'])} topic preview group(s).")

        for topic_group in data["topics"]:
            print(f"\n   [Topic: {topic_group['topic_name']}] ({topic_group['scope']})")
            articles = topic_group.get("articles", [])
            print(f"   Articles fetched: {len(articles)}")
            for art in articles[:2]:
                print(f"     • {art['title'][:55]}... ({art['source']})")
                print(f"       Summary: {art['summary'][:90]}...")

    await close_mongo_connection()
    print("\n[SUCCESS] Phase 3 Live News Preview API test passed completely!")

if __name__ == "__main__":
    asyncio.run(run_test())
