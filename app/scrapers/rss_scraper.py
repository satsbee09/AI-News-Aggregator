import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import feedparser
from app.scrapers.base import BaseScraper, ScrapedArticle

DEFAULT_FEEDS: Dict[str, str] = {
    "openai": "https://openai.com/news/rss.xml",
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "simon_willison_ai": "https://simonwillison.net/atom/everything/",
    "techcrunch_ai": "https://techcrunch.com/category/artificial-intelligence/feed/"
}

class RssScraper(BaseScraper):
    def __init__(self, feeds: Dict[str, str] = DEFAULT_FEEDS):
        self.feeds = feeds

    def _clean_html(self, raw_html: str) -> str:
        """Removes HTML tags and normalizes whitespace."""
        clean_text = re.sub(r"<[^>]+>", " ", raw_html)
        return " ".join(clean_text.split())

    def _parse_published_date(self, entry) -> datetime:
        """Extracts UTC datetime from feedparser entry."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    def get_articles(self, hours: int = 48) -> List[ScrapedArticle]:
        articles: List[ScrapedArticle] = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours) if hours > 0 else None

        for source_name, feed_url in self.feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo and not feed.entries:
                    print(f"   [WARN] Failed to parse feed for {source_name}: {feed_url}")
                    continue

                for entry in feed.entries:
                    published_at = self._parse_published_date(entry)

                    # Filter by cutoff time if specified
                    if cutoff_time and published_at < cutoff_time:
                        continue

                    title = getattr(entry, "title", "Untitled")
                    url = getattr(entry, "link", "")
                    if not url:
                        continue

                    # Extract content (summary or full content)
                    content = ""
                    if hasattr(entry, "content") and entry.content:
                        content = entry.content[0].value
                    elif hasattr(entry, "summary") and entry.summary:
                        content = entry.summary

                    cleaned_content = self._clean_html(content) if content else title

                    articles.append(
                        ScrapedArticle(
                            title=title,
                            url=url,
                            source=source_name,
                            raw_content=cleaned_content,
                            published_at=published_at
                        )
                    )
            except Exception as e:
                print(f"   [ERROR] Error scraping {source_name}: {e}")

        return articles
