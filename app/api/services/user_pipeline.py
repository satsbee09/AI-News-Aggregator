import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.api.database import get_users_collection
from app.database.repository import MongoRepository
from app.scrapers.base import BaseScraper
from app.scrapers.google_news_scraper import GoogleNewsScraper
from app.scrapers.weather_scraper import WeatherScraper
from app.scrapers.rss_scraper import RssScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.services.process_digest import process_unprocessed_digests
from app.agent.curator_agent import CuratorAgent
from app.services.email_service import send_digest_email
from app.profiles.user_profile import UserProfile

def build_scrapers_for_user_topics(topics: List[Dict[str, Any]]) -> List[BaseScraper]:
    """Constructs dynamic scrapers specifically for a user's chosen topics."""
    scrapers: List[BaseScraper] = []
    
    # Always include tech/AI scrapers if user selected AI
    has_ai = any(t.get("scope") == "ai" or "ai" in t.get("name", "").lower() for t in topics)
    if has_ai:
        scrapers.append(RssScraper())
        scrapers.append(YouTubeScraper())

    for t in topics:
        name = t.get("name", "").strip()
        scope = t.get("scope", "general").lower()
        category = t.get("category", scope)
        
        if not name:
            continue
            
        if scope == "weather" or "weather" in name.lower():
            city = name.replace("Weather", "").replace("weather", "").replace("NCR", "").replace("ncr", "").strip() or "Delhi"
            scrapers.append(WeatherScraper(city_name=city, topic_name=name))
        elif scope == "ai" and name in ["Frontier AI & LLMs", "AI"]:
            # Handled by static RSS & YouTube scrapers above
            continue
        else:
            scrapers.append(GoogleNewsScraper(query=name, topic_name=name, category=category))

    return scrapers

async def run_user_pipeline(email: str, topics: Optional[List[Dict[str, Any]]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Runs the full intelligence pipeline parameterized for a specific user's topics and destination email."""
    print(f"\n=================================================================")
    print(f"[PIPELINE TRIGGER] Running personalized pipeline for: {email}")
    print(f"=================================================================")
    
    if not topics:
        try:
            users_col = get_users_collection()
            user_doc = await users_col.find_one({"email": email.lower().strip()})
            if user_doc:
                topics = user_doc.get("topics", [])
        except Exception as e:
            print(f"[WARN] Error fetching user doc: {e}")
        
    if not topics:
        print(f"[WARN] User '{email}' has no selected topics.")
        return {"status": "error", "message": "No topics configured for user."}

    repo = MongoRepository()
    
    # Step 1: Ingestion
    scrapers = build_scrapers_for_user_topics(topics)
    print(f"Step 1: Running {len(scrapers)} scrapers for user topics...")
    loop = asyncio.get_running_loop()
    
    def _run_scrapers():
        total_saved = 0
        for scraper in scrapers:
            try:
                articles = scraper.get_articles(hours=48)
                for a in articles:
                    saved = repo.save_article(
                        title=a.title,
                        url=a.url,
                        source=a.source,
                        category=getattr(a, "category", "general"),
                        topic_name=getattr(a, "topic_name", "General News"),
                        raw_content=a.raw_content,
                        published_at=a.published_at
                    )
                    if saved:
                        total_saved += 1
            except Exception as e:
                print(f"[SCRAPER ERROR] {scraper}: {e}")
        return total_saved

    saved_count = await loop.run_in_executor(None, _run_scrapers)
    print(f"Saved {saved_count} new articles to database.")

    # Step 2: Groq LLM Summarization
    print("Step 2: Processing unprocessed digests with Groq LLM...")
    def _run_summaries():
        return process_unprocessed_digests(repo=repo, limit=8)
        
    processed_count = await loop.run_in_executor(None, _run_summaries)
    print(f"Generated {processed_count} new digests.")

    # Step 3: Curation
    print("Step 3: Curating top stories for user...")
    unsent_digests = repo.get_unsent_digests()
    if not unsent_digests:
        print("[INFO] No unsent digests available.")
        return {"status": "success", "message": "No new unsent content to email."}

    custom_profile = UserProfile(
        name=email.split("@")[0].capitalize(),
        primary_interests=[t.get("name", "") for t in topics],
        max_daily_articles=5
    )


    curator = CuratorAgent()
    ranked = curator.rank_digests(unsent_digests, profile=custom_profile)
    top_stories = ranked[:custom_profile.max_daily_articles]

    # Step 4: Dispatch Email
    print(f"Step 4: Dispatching categorized email to {email}...")
    def _send_email():
        return send_digest_email(ranked_items=top_stories, repo=repo, recipient=email, dry_run=dry_run)

    success = await loop.run_in_executor(None, _send_email)
    print(f"[RESULT] User pipeline completed. Email sent: {success}")
    
    return {
        "status": "success" if success else "failed",
        "email": email,
        "articles_saved": saved_count,
        "digests_generated": processed_count,
        "stories_curated": len(top_stories),
        "email_sent": success
    }
