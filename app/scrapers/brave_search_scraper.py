import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.scrapers.base import BaseScraper, ScrapedArticle
from app.config import settings

class BraveSearchScraper(BaseScraper):
    def __init__(
        self,
        query: str,
        topic_name: str = "General News",
        category: str = "general"
    ):
        self.query = query
        self.topic_name = topic_name
        self.category = category
        self.api_key = settings.BRAVE_API_KEY

    def get_articles(self, hours: int = 48) -> List[ScrapedArticle]:
        if not self.api_key:
            return []

        articles: List[ScrapedArticle] = []
        now = datetime.now(timezone.utc)
        endpoint = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": f"{self.query} news",
            "count": 10
        }

        try:
            res = requests.get(endpoint, headers=headers, params=params, timeout=6)
            if not res.ok:
                return []

            data = res.json()
            web_results = data.get("web", {}).get("results", [])
            for item in web_results:
                title = item.get("title", "").strip()
                url = item.get("url", "")
                snippet = item.get("description", "").strip()
                if not url or not title:
                    continue

                articles.append(
                    ScrapedArticle(
                        title=title,
                        url=url,
                        source="brave_search",
                        category=self.category,
                        topic_name=self.topic_name,
                        raw_content=snippet,
                        published_at=now
                    )
                )
        except Exception as e:
            print(f"   [ERROR] BraveSearchScraper failed for query '{self.query}': {e}")

        return articles
