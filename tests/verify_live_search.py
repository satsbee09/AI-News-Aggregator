import urllib.request
import json

queries = ["Virat Kohli", "Apple M4 chip", "Sensex Nifty stock market", "Delhi monsoon weather"]

for query in queries:
    req = urllib.request.Request(
        'http://localhost:5000/api/search/live',
        data=json.dumps({'query': query}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
        print(f"\n==========================================")
        print(f"SEARCH QUERY: '{query}' | Results: {data.get('count')}")
        print(f"==========================================")
        for r in data.get('results', [])[:4]:
            print(f"  * {r.get('title')} [{r.get('source')}]")
            print(f"    URL: {r.get('url')[:80]}...")
