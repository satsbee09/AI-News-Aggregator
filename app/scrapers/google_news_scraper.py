import re
import urllib.parse
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import feedparser
from app.scrapers.base import BaseScraper, ScrapedArticle
from app.config import settings

class GoogleNewsScraper(BaseScraper):
    def __init__(
        self,
        query: str,
        topic_name: str = "General News",
        category: str = "general",
        hl: str = "en-IN",
        gl: str = "IN",
        ceid: str = "IN:en"
    ):
        self.query = query
        self.topic_name = topic_name
        self.category = category
        self.hl = hl
        self.gl = gl
        self.ceid = ceid

    def _clean_html(self, raw_html: str) -> str:
        clean_text = re.sub(r"<[^>]+>", " ", raw_html or "")
        return " ".join(clean_text.split())

    def get_articles(self, hours: int = 48) -> List[ScrapedArticle]:
        articles: List[ScrapedArticle] = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours) if hours > 0 else None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        # 1. Google Custom Search JSON API (if configured & enabled)
        if settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_ID:
            try:
                endpoint = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": settings.GOOGLE_CSE_API_KEY,
                    "cx": settings.GOOGLE_CSE_ID,
                    "q": self.query,
                    "num": 8
                }
                res = requests.get(endpoint, params=params, timeout=6)
                if res.ok:
                    items = res.json().get("items", [])
                    for item in items:
                        articles.append(
                            ScrapedArticle(
                                title=item.get("title", "").strip(),
                                url=item.get("link", ""),
                                source="google_search_api",
                                category=self.category,
                                topic_name=self.topic_name,
                                raw_content=self._clean_html(item.get("snippet", "")),
                                published_at=now
                            )
                        )
                    if articles:
                        return articles
            except Exception as e:
                pass  # Fallback to Google News RSS

        # 2. Google News Real-Time RSS Stream
        candidate_queries = [
            f"when:24h {self.query}",
            f"when:7d {self.query}",
            f"when:30d {self.query}",
            self.query
        ]

        for cand in candidate_queries:
            try:
                encoded = urllib.parse.quote_plus(cand)
                feed_url = f"https://news.google.com/rss/search?q={encoded}"
                res = requests.get(feed_url, headers=headers, timeout=6)
                if not res.ok:
                    continue

                feed = feedparser.parse(res.content)
                if not feed.entries:
                    continue

                for entry in feed.entries[:10]:
                    published_at = now
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    if cutoff_time and published_at < cutoff_time:
                        continue

                    title = getattr(entry, "title", "Untitled")
                    url = getattr(entry, "link", "")
                    if not url:
                        continue

                    raw_summary = getattr(entry, "summary", title)
                    content = self._clean_html(raw_summary)

                    source_name = "google_news"
                    if " - " in title:
                        source_name = f"gnews_{title.rsplit(' - ', 1)[-1].strip().lower().replace(' ', '_')}"

                    articles.append(
                        ScrapedArticle(
                            title=title,
                            url=url,
                            source=source_name,
                            category=self.category,
                            topic_name=self.topic_name,
                            raw_content=content,
                            published_at=published_at
                        )
                    )

                if articles:
                    return articles
            except Exception as e:
                print(f"   [ERROR] GoogleNewsScraper candidate '{cand}' failed: {e}")
                continue

        return articles
