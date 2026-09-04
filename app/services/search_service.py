import logging
import requests
import re
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import feedparser
from app.config import settings

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_CSE_API_KEY
        self.google_cse_id = settings.GOOGLE_CSE_ID
        self.brave_api_key = settings.BRAVE_API_KEY
        
        # In-memory quota tracker for Google Search (100 free queries/day threshold)
        self.google_quota_date = date.today()
        self.google_query_count = 0
        self.google_daily_limit = 90

    def _check_and_reset_quota(self):
        today = date.today()
        if today != self.google_quota_date:
            self.google_quota_date = today
            self.google_query_count = 0

    def _clean_html(self, text: str) -> str:
        clean = re.sub(r'<[^>]+>', ' ', text or '')
        return ' '.join(clean.split())

    def google_search(self, query: str, num_results: int = 6) -> List[Dict[str, Any]]:
        """Executes search via Google Custom Search JSON API."""
        if not self.google_api_key or not self.google_cse_id:
            raise ValueError("Google Custom Search API Key or CX ID is missing.")

        self._check_and_reset_quota()
        if self.google_query_count >= self.google_daily_limit:
            raise RuntimeError(f"Google daily quota threshold reached ({self.google_query_count}/{self.google_daily_limit}).")

        endpoint = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": min(num_results, 10)
        }

        response = requests.get(endpoint, params=params, timeout=8)
        if not response.ok:
            raise RuntimeError(f"Google CSE error {response.status_code}: {response.text[:150]}")

        self.google_query_count += 1
        data = response.json()
        items = data.get("items", [])
        
        results = []
        for item in items[:num_results]:
            results.append({
                "title": item.get("title", "").strip(),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "").strip(),
                "source": "google_search",
                "published": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")
            })
        return results

    def brave_search(self, query: str, num_results: int = 6) -> List[Dict[str, Any]]:
        """Executes search via Brave Search API."""
        if not self.brave_api_key:
            raise ValueError("Brave Search API Key is missing.")

        endpoint = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": min(num_results, 10)
        }

        response = requests.get(endpoint, headers=headers, params=params, timeout=8)
        if not response.ok:
            raise RuntimeError(f"Brave Search API error {response.status_code}: {response.text[:150]}")

        data = response.json()
        web_results = data.get("web", {}).get("results", [])
        results = []
        for item in web_results[:num_results]:
            results.append({
                "title": item.get("title", "").strip(),
                "url": item.get("url", ""),
                "snippet": item.get("description", "").strip(),
                "source": "brave_search",
                "published": item.get("page_age")
            })
        return results

    def google_news_search(self, query: str, num_results: int = 6) -> List[Dict[str, Any]]:
        """Searches Google News RSS feeds for the EXACT keyword/entity."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        # Google News RSS yields maximal results with time-windowing or news queries
        candidate_queries = [
            f"when:24h {query}",
            f"when:7d {query}",
            f"when:30d {query}",
            query
        ]
        
        for cand in candidate_queries:
            try:
                encoded = urllib.parse.quote_plus(cand)
                search_url = f"https://news.google.com/rss/search?q={encoded}"
                res = requests.get(search_url, headers=headers, timeout=6)
                if not res.ok:
                    continue
                
                feed = feedparser.parse(res.content)
                if not feed.entries:
                    continue
                
                results = []
                for entry in feed.entries[:num_results]:
                    title = getattr(entry, "title", "Untitled")
                    url = getattr(entry, "link", "")
                    raw_summary = getattr(entry, "summary", title)
                    
                    # Extract source outlet from title format: "Article Title - Outlet"
                    source_tag = "google_news"
                    if " - " in title:
                        source_tag = f"gnews_{title.rsplit(' - ', 1)[-1].strip().lower().replace(' ', '_')}"

                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": self._clean_html(raw_summary),
                        "source": source_tag,
                        "published": getattr(entry, "published", None)
                    })
                
                if results:
                    return results
            except Exception as e:
                logger.debug(f"[SEARCH] Google News candidate '{cand}' failed: {e}")
                continue
                
        return []

    def bing_news_search(self, query: str, num_results: int = 6) -> List[Dict[str, Any]]:
        """Searches Bing News RSS feeds for the EXACT keyword/entity."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.bing.com/news/search?q={encoded}&format=rss"
        
        res = requests.get(search_url, headers=headers, timeout=6)
        if not res.ok:
            return []

        feed = feedparser.parse(res.content)
        results = []
        for entry in feed.entries[:num_results]:
            title = getattr(entry, "title", "Untitled")
            url = getattr(entry, "link", "")
            raw_summary = getattr(entry, "summary", title)
            results.append({
                "title": title,
                "url": url,
                "snippet": self._clean_html(raw_summary),
                "source": "bing_news",
                "published": getattr(entry, "published", None)
            })
        return results

    def live_search(
        self,
        query: str,
        topic: Optional[str] = None,
        num_results: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Public entry point for live web search:
        Searches for the EXACT user query across multiple resilient engines:
        1. Google Custom Search (if key active)
        2. Brave Search API (if key active)
        3. Google News Real-Time RSS Search
        4. Bing News Real-Time RSS Search
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # 1. Try Google Custom Search API
        try:
            results = self.google_search(clean_query, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Google Search returned {len(results)} results for: '{clean_query}'")
                return results
        except Exception as e:
            logger.debug(f"[SEARCH] Google Search unavailable: {e}")

        # 2. Try Brave Search API
        try:
            results = self.brave_search(clean_query, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Brave Search returned {len(results)} results for: '{clean_query}'")
                return results
        except Exception as e:
            logger.debug(f"[SEARCH] Brave Search unavailable: {e}")

        # 3. Try Google News RSS for the exact query
        try:
            results = self.google_news_search(clean_query, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Google News RSS returned {len(results)} results for: '{clean_query}'")
                return results
        except Exception as e:
            logger.debug(f"[SEARCH] Google News RSS error: {e}")

        # 4. Try Bing News RSS for the exact query
        try:
            results = self.bing_news_search(clean_query, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Bing News RSS returned {len(results)} results for: '{clean_query}'")
                return results
        except Exception as e:
            logger.debug(f"[SEARCH] Bing News RSS error: {e}")

        logger.warning(f"[SEARCH EXHAUSTED] No live news results found for: '{clean_query}'.")
        return []

search_service = SearchService()
