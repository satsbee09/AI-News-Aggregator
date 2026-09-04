from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class ScrapedArticle:
    title: str
    url: str
    source: str
    raw_content: str
    category: str = "general"
    topic_name: str = "General News"
    published_at: Optional[datetime] = None

class BaseScraper(ABC):
    """Abstract Base Scraper interface that all concrete scrapers must implement."""

    @abstractmethod
    def get_articles(self, hours: int = 24) -> List[ScrapedArticle]:
        """
        Fetches articles published in the last `hours`.
        If hours == 0, returns the latest available items without time filtering.
        """
        pass
