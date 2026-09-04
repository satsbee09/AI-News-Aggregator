import requests
import json
from app.config import settings
from app.services.search_service import search_service

print("==================================================")
print("1. CHECKING GOOGLE CUSTOM SEARCH JSON API (API KEY)")
print("==================================================")
print(f"API Key: {settings.GOOGLE_CSE_API_KEY[:10]}... (Total len: {len(settings.GOOGLE_CSE_API_KEY)})")
print(f"Search Engine CX ID: {settings.GOOGLE_CSE_ID}")

try:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.GOOGLE_CSE_API_KEY,
        "cx": settings.GOOGLE_CSE_ID,
        "q": "latest technology news"
    }
    resp = requests.get(url, params=params, timeout=6)
    print(f"HTTP Status: {resp.status_code}")
    data = resp.json()
    if resp.ok:
        items = data.get("items", [])
        print(f"[SUCCESS] Google Custom Search API returned {len(items)} results:")
        for item in items[:3]:
            print(f"  * {item.get('title')} ({item.get('link')})")
    else:
        print("[FAIL] Google Cloud API Error:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"[ERROR] Exception occurred: {e}")

print("\n==================================================")
print("2. CHECKING GOOGLE NEWS REAL-TIME SEARCH (BUILT-IN)")
print("==================================================")
for query in ["Google AI Gemini", "Virat Kohli", "ISRO latest launch"]:
    results = search_service.google_news_search(query, num_results=3)
    print(f"\nQuery: '{query}' -> Found {len(results)} articles from Google:")
    for r in results:
        print(f"  * {r['title']} [{r['source']}]")
