import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date
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
        self.google_daily_limit = 90  # Proactively switch to Brave after 90 queries

    def _check_and_reset_quota(self):
        """Resets the daily quota counter if a new calendar day has started."""
        today = date.today()
        if today != self.google_quota_date:
            self.google_quota_date = today
            self.google_query_count = 0
            logger.info("[SEARCH SERVICE] Google CSE daily query counter reset for new day.")

    def google_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes search via Google Custom Search JSON API.
        Returns normalized list: [{title, url, snippet, source: 'google'}]
        """
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

        response = requests.get(endpoint, params=params, timeout=10)
        
        if response.status_code == 429:
            raise RuntimeError("Google Custom Search API returned 429 Too Many Requests.")
        
        if not response.ok:
            raise RuntimeError(f"Google Custom Search API error {response.status_code}: {response.text[:200]}")

        self.google_query_count += 1
        data = response.json()
        items = data.get("items", [])
        
        results = []
        for item in items[:num_results]:
            results.append({
                "title": item.get("title", "").strip(),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "").strip(),
                "source": "google",
                "published": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")
            })

        return results

    def brave_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes search via Brave Search API.
        Returns normalized list: [{title, url, snippet, source: 'brave'}]
        """
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

        response = requests.get(endpoint, headers=headers, params=params, timeout=10)

        if response.status_code == 429:
            raise RuntimeError("Brave Search API returned 429 Rate Limit Exceeded.")

        if not response.ok:
            raise RuntimeError(f"Brave Search API error {response.status_code}: {response.text[:200]}")

        data = response.json()
        web_results = data.get("web", {}).get("results", [])

        results = []
        for item in web_results[:num_results]:
            results.append({
                "title": item.get("title", "").strip(),
                "url": item.get("url", ""),
                "snippet": item.get("description", "").strip(),
                "source": "brave",
                "published": item.get("page_age")
            })

        return results

    def live_search(
        self,
        query: str,
        topic: Optional[str] = None,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Public entry point for live web search:
        1. Appends topic keyword if provided (e.g. query='Noida', topic='local' -> 'Noida local news').
        2. Tries Google Custom Search first.
        3. Automatically falls back to Brave Search if Google errors, hits 429, or quota limit.
        4. If both fail or no keys are configured, safely returns empty list without crashing.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Contextually enrich query if topic is specified
        search_term = clean_query
        if topic and topic.lower() not in clean_query.lower():
            topic_clean = topic.lower().replace("frontier ", "").replace("news", "").strip()
            search_term = f"{clean_query} {topic_clean} news".strip()

        # Step 1: Try Google Search
        try:
            results = self.google_search(search_term, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Google Search returned {len(results)} results for: '{search_term}'")
                return results
        except Exception as e:
            logger.warning(f"[SEARCH FALLBACK] Google Search unavailable ({e}). Falling back to Brave Search...")

        # Step 2: Fallback to Brave Search
        try:
            results = self.brave_search(search_term, num_results=num_results)
            if results:
                logger.info(f"[SEARCH SUCCESS] Brave Search returned {len(results)} results for: '{search_term}'")
                return results
        except Exception as e:
            logger.warning(f"[SEARCH FALLBACK] Brave Search failed ({e}).")

        # Step 3: Graceful empty return
        logger.warning(f"[SEARCH EXHAUSTED] No live search results retrieved for: '{search_term}'.")
        return []

search_service = SearchService()
