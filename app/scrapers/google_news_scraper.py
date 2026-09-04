import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import feedparser
from app.scrapers.base import BaseScraper, ScrapedArticle

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
        clean_text = re.sub(r"<[^>]+>", " ", raw_html)
        return " ".join(clean_text.split())

    def get_articles(self, hours: int = 48) -> List[ScrapedArticle]:
        encoded_query = urllib.parse.quote_plus(self.query)
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={self.hl}&gl={self.gl}&ceid={self.ceid}"
        
        articles: List[ScrapedArticle] = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours) if hours > 0 else None

        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:  # Limit top 10 per topic query
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

                # Extract source name from Google News title format "Title - Source"
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
        except Exception as e:
            print(f"   [ERROR] GoogleNewsScraper failed for query '{self.query}': {e}")

        return articles
