import requests
import json
from app.config import settings

def test_brave():
    print("Testing Brave Web Search...")
    endpoint = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.BRAVE_API_KEY
    }
    r = requests.get(endpoint, headers=headers, params={"q": "Virat Kohli", "count": 5})
    print("Status:", r.status_code)
    try:
        data = r.json()
        print("Data keys:", list(data.keys()))
        if "web" in data:
            print("Web results count:", len(data["web"].get("results", [])))
            for res in data["web"].get("results", [])[:3]:
                print(" - Web:", res.get("title"), "->", res.get("url"))
        if "news" in data:
            print("News cluster count:", len(data["news"].get("results", [])))
            for res in data["news"].get("results", [])[:3]:
                print(" - News:", res.get("title"), "->", res.get("url"))
    except Exception as e:
        print("JSON parse error:", e, r.text[:300])

def test_brave_news():
    print("\nTesting Brave Dedicated News API...")
    endpoint = "https://api.search.brave.com/res/v1/news/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.BRAVE_API_KEY
    }
    r = requests.get(endpoint, headers=headers, params={"q": "Virat Kohli", "count": 5})
    print("Status:", r.status_code)
    try:
        data = r.json()
        print("News keys:", list(data.keys()))
        results = data.get("results", [])
        print("Dedicated News results count:", len(results))
        for res in results[:3]:
            print(" - News item:", res.get("title"), "->", res.get("url"))
    except Exception as e:
        print("JSON parse error:", e, r.text[:300])

if __name__ == "__main__":
    test_brave()
    test_brave_news()
