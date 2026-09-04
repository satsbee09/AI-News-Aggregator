import time
from datetime import datetime, timezone
from typing import List
from app.database.mongo import init_mongo_db
from app.database.repository import MongoRepository
from app.scrapers.base import BaseScraper
from app.scrapers.rss_scraper import RssScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.google_news_scraper import GoogleNewsScraper
from app.scrapers.weather_scraper import WeatherScraper
from app.services.process_digest import process_unprocessed_digests
from app.agent.curator_agent import CuratorAgent
from app.services.email_service import send_digest_email
from app.profiles.user_profile import DEFAULT_USER_PROFILE

def build_dynamic_scrapers(topics: List[dict]) -> List[BaseScraper]:
    """Dynamically instantiates scrapers based on active topics in MongoDB."""
    scrapers: List[BaseScraper] = [
        RssScraper(),       # Static AI Research Feeds
        YouTubeScraper()    # Static AI YouTube Channels
    ]

    for t in topics:
        scope = t.get("scope", "general")
        category = t.get("category", "general")
        topic_name = t.get("topic_name", "General News")
        query = t.get("query", topic_name)
        location = t.get("location", "")

        if scope == "weather":
            city = location.split(",")[0].strip() if location else query
            scrapers.append(WeatherScraper(city_name=city or "Delhi", topic_name=topic_name))
        else:
            # Build Google News Scraper for this topic
            scrapers.append(
                GoogleNewsScraper(
                    query=query,
                    topic_name=topic_name,
                    category=category
                )
            )

    return scrapers

def run_daily_pipeline(
    hours: int = 48,
    limit: int = 15,
    dry_run: bool = False,
    scrape_only: bool = False
) -> bool:
    """
    Orchestrates the entire universal multi-topic daily workflow:
    1. Ensures MongoDB collections & indexes exist, seeds topics
    2. Builds dynamic scrapers per active topic & persists to MongoDB
    3. Runs LLM summarization on new articles
    4. Ranks & curates top stories across topics per user weighting
    5. Delivers categorized HTML email newsletter & logs sent status
    """
    start_time = time.time()
    print("=" * 65)
    print(f"[START] UNIVERSAL NEWS INTELLIGENCE PIPELINE [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}]")
    print("=" * 65)

    # 1. Initialize MongoDB
    init_mongo_db()
    repo = MongoRepository()

    # 2. Dynamic Scraper Construction
    active_topics = repo.get_active_topics()
    print(f"\n[STEP 1/4] Loaded {len(active_topics)} active user topics. Building dynamic scrapers...")
    dynamic_scrapers = build_dynamic_scrapers(active_topics)
    print(f"   Instantiated {len(dynamic_scrapers)} total active scrapers.")

    total_new_articles = 0
    total_duplicates = 0

    for scraper in dynamic_scrapers:
        scraper_name = scraper.__class__.__name__
        desc = getattr(scraper, "topic_name", scraper_name)
        print(f"   -> Running {scraper_name} [{desc}]...")
        try:
            articles = scraper.get_articles(hours=hours)
            for a in articles:
                saved = repo.save_article(
                    title=a.title,
                    url=a.url,
                    source=a.source,
                    category=a.category,
                    topic_name=a.topic_name,
                    raw_content=a.raw_content,
                    published_at=a.published_at
                )
                if saved:
                    total_new_articles += 1
                else:
                    total_duplicates += 1
        except Exception as e:
            print(f"   [ERROR] Scraper {scraper_name} failed: {e}")

    print(f"   [RESULT] Ingestion complete: {total_new_articles} newly saved, {total_duplicates} existing skipped.")

    if scrape_only:
        print("\n[INFO] --scrape-only flag set. Stopping pipeline after scraping.")
        return True

    # 3. LLM Summarization Layer
    print(f"\n[STEP 2/4] Generating Multi-Topic AI Summaries with Groq LLM (Limit: {limit})...")
    processed_digests_count = process_unprocessed_digests(repo=repo, limit=limit)
    print(f"   [RESULT] Generated {processed_digests_count} new digest(s).")

    # 4. Curation & Relevance Ranking Layer
    print("\n[STEP 3/4] Curating & Ranking unsent digests across categories...")
    unsent_digests = repo.get_unsent_digests()
    print(f"   Found {len(unsent_digests)} total unsent digest(s) in MongoDB.")

    if not unsent_digests:
        print("   [INFO] No unsent digests available to email today. Pipeline complete!")
        return True

    # Build topic weight dictionary from active topics
    topic_weights = {t["topic_name"]: t.get("weight", 1.0) for t in active_topics}
    for t in active_topics:
        topic_weights[t.get("category", "")] = t.get("weight", 1.0)

    curator = CuratorAgent()
    ranked_stories = curator.rank_digests(unsent_digests, profile=DEFAULT_USER_PROFILE, topic_weights=topic_weights)
    top_stories = ranked_stories[:DEFAULT_USER_PROFILE.max_daily_articles]

    print(f"\n   --- Today's Top {len(top_stories)} Selected Stories ---")
    for rank, (digest, score, reason) in enumerate(top_stories, start=1):
        article = digest.get("article", {})
        safe_title = article.get('title', '').encode('ascii', 'replace').decode('ascii')[:50]
        print(f"   #{rank} [Score: {score}] [{digest.get('category', '').upper()}] {safe_title}...")

    # 5. Email Packaging & Delivery Layer
    print(f"\n[STEP 4/4] Packaging & Delivering Categorized Email Digest (Dry Run: {dry_run})...")
    email_success = send_digest_email(ranked_items=top_stories, repo=repo, dry_run=dry_run)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 65)
    if email_success:
        print(f"[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s!")
    else:
        print(f"[WARN] PIPELINE FINISHED WITH WARNINGS IN {elapsed}s")
    print("=" * 65)
    return email_success
