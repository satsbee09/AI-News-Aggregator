import time
from datetime import datetime, timezone
from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository
from app.scrapers.base import BaseScraper
from app.scrapers.rss_scraper import RssScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.services.process_digest import process_unprocessed_digests
from app.agent.curator_agent import CuratorAgent
from app.services.email_service import send_digest_email
from app.profiles.user_profile import DEFAULT_USER_PROFILE

# All active content scrapers
SCRAPER_REGISTRY: list[BaseScraper] = [
    RssScraper(),
    YouTubeScraper()
]

def run_daily_pipeline(
    hours: int = 48,
    limit: int = 10,
    dry_run: bool = False,
    scrape_only: bool = False
) -> bool:
    """
    Orchestrates the entire daily workflow:
    1. Ensures DB tables exist
    2. Scrapes all registered sources & deduplicates in DB
    3. Runs LLM summarization on new articles
    4. Ranks & curates top stories against User Profile
    5. Delivers styled HTML email and logs sent status
    """
    start_time = time.time()
    print("=" * 65)
    print(f"🚀 STARTING AI NEWS INTELLIGENCE PIPELINE [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}]")
    print("=" * 65)

    # 1. Initialize Database
    init_db()
    session = SessionLocal()
    repo = Repository(session)

    # 2. Ingestion / Scraping Layer
    print(f"\n[STEP 1/4] Scraping content sources (Lookback: {hours}h)...")
    total_new_articles = 0
    total_duplicates = 0

    for scraper in SCRAPER_REGISTRY:
        scraper_name = scraper.__class__.__name__
        print(f"   -> Running {scraper_name}...")
        try:
            articles = scraper.get_articles(hours=hours)
            for a in articles:
                saved = repo.save_article(
                    title=a.title,
                    url=a.url,
                    source=a.source,
                    raw_content=a.raw_content,
                    published_at=a.published_at
                )
                if saved:
                    total_new_articles += 1
                else:
                    total_duplicates += 1
        except Exception as e:
            print(f"   [ERROR] Scraper {scraper_name} failed: {e}")

    print(f"   [RESULT] Scraping complete: {total_new_articles} newly saved, {total_duplicates} existing skipped.")

    if scrape_only:
        print("\n[INFO] --scrape-only flag set. Stopping pipeline after scraping.")
        session.close()
        return True

    # 3. LLM Summarization Layer
    print(f"\n[STEP 2/4] Generating AI Summaries with Groq LLM (Limit: {limit})...")
    processed_digests_count = process_unprocessed_digests(session=session, limit=limit)
    print(f"   [RESULT] Generated {processed_digests_count} new digest(s).")

    # 4. Curation & Relevance Ranking Layer
    print("\n[STEP 3/4] Curating & Ranking unsent digests...")
    unsent_digests = repo.get_unsent_digests()
    print(f"   Found {len(unsent_digests)} total unsent digest(s) in database.")

    if not unsent_digests:
        print("   [INFO] No unsent digests available to email today. Pipeline complete!")
        session.close()
        return True

    curator = CuratorAgent()
    ranked_stories = curator.rank_digests(unsent_digests, profile=DEFAULT_USER_PROFILE)
    top_stories = ranked_stories[:DEFAULT_USER_PROFILE.max_daily_articles]

    print(f"\n   --- Today's Top {len(top_stories)} Selected Stories ---")
    for rank, (digest, score, reason) in enumerate(top_stories, start=1):
        print(f"   #{rank} [{score}/10] [{digest.category}] {digest.article.title[:50]}...")

    # 5. Email Packaging & Delivery Layer
    print(f"\n[STEP 4/4] Packaging & Delivering Email Digest (Dry Run: {dry_run})...")
    email_success = send_digest_email(session=session, ranked_items=top_stories, dry_run=dry_run)

    session.close()
    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 65)
    if email_success:
        print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s!")
    else:
        print(f"⚠️ PIPELINE FINISHED WITH WARNINGS IN {elapsed}s")
    print("=" * 65)
    return email_success
