import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from app.scrapers.google_news_scraper import GoogleNewsScraper
from app.scrapers.weather_scraper import WeatherScraper
from app.scrapers.rss_scraper import RssScraper
from app.agent.digest_agent import DigestAgent
from app.api.schemas import TopicItem

executor = ThreadPoolExecutor(max_workers=5)

def _scrape_and_summarize_topic(topic: TopicItem, agent: DigestAgent) -> Dict[str, Any]:
    """Synchronously fetches recent articles and quick summaries for a single topic."""
    name = topic.name.strip()
    scope = topic.scope.lower()
    articles_data = []

    try:
        if scope == "weather" or "weather" in name.lower():
            city = name.replace("Weather", "").replace("weather", "").replace("NCR", "").replace("ncr", "").strip() or "Delhi"
            scraper = WeatherScraper(city_name=city, topic_name=name)
            scraped = scraper.get_articles()[:2]
            for a in scraped:
                summary = a.raw_content.split("\n")[0] if "\n" in a.raw_content else a.raw_content
                articles_data.append({
                    "title": a.title,
                    "url": a.url,
                    "source": a.source,
                    "summary": summary,
                    "key_takeaways": [line.strip() for line in a.raw_content.split("\n")[1:] if line.strip()],
                    "published_at": a.published_at.isoformat() if a.published_at else None
                })
        else:
            scraper = GoogleNewsScraper(query=name, topic_name=name, category=scope)
            scraped = scraper.get_articles(hours=48)[:3]
            
            # Fallback if no fresh news in last 48h
            if not scraped:
                scraped = scraper.get_articles(hours=168)[:2]

            for a in scraped:
                # Fast summary with LLM or fallback snippet
                summary = ""
                takeaways = []
                try:
                    digest = agent.summarize(title=a.title, source=a.source, raw_content=a.raw_content)
                    summary = digest.summary
                    takeaways = digest.key_takeaways
                except Exception:
                    summary = a.raw_content[:250] + ("..." if len(a.raw_content) > 250 else "")
                    takeaways = ["Live preview summary"]

                articles_data.append({
                    "title": a.title,
                    "url": a.url,
                    "source": a.source,
                    "summary": summary,
                    "key_takeaways": takeaways,
                    "published_at": a.published_at.isoformat() if a.published_at else None
                })
    except Exception as e:
        print(f"[PREVIEW ERROR] Failed to fetch topic '{name}': {e}")

    return {
        "topic_name": name,
        "scope": scope,
        "category": topic.category or scope,
        "articles": articles_data
    }

async def fetch_news_preview(topics: List[TopicItem]) -> Dict[str, Any]:
    """Fetches instant on-demand news preview across multiple topics concurrently."""
    agent = DigestAgent()
    loop = asyncio.get_running_loop()
    
    tasks = [
        loop.run_in_executor(executor, _scrape_and_summarize_topic, topic, agent)
        for topic in topics
    ]
    
    results = await asyncio.gather(*tasks)
    return {"topics": results}
