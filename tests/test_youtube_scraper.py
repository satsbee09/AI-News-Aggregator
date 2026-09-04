from app.database.mongo import init_mongo_db
from app.database.repository import MongoRepository
from app.scrapers.youtube_scraper import YouTubeScraper

def run_test():
    print("1. Initializing MongoDB...")
    init_mongo_db()
    repo = MongoRepository()

    print("\n2. Fetching recent YouTube videos & transcripts (last 72 hours)...")
    scraper = YouTubeScraper()
    videos = scraper.get_articles(hours=72)
    print(f"   [SUCCESS] Scraped {len(videos)} video(s) from YouTube channels.")

    # Fallback to latest available if no videos in the last 72 hours
    if not videos:
        print("   [INFO] No videos in last 72h. Fetching latest 3 videos across channels...")
        videos = scraper.get_articles(hours=0)[:3]
        print(f"   [SUCCESS] Scraped {len(videos)} latest video(s).")

    assert len(videos) > 0, "Failed: Could not scrape any YouTube videos."

    print("\n3. Saving scraped videos to MongoDB database...")
    saved_count = 0
    duplicate_count = 0
    for v in videos:
        saved = repo.save_article(
            title=v.title,
            url=v.url,
            source=v.source,
            category=getattr(v, "category", "ai"),
            topic_name=getattr(v, "topic_name", "AI YouTube Intel"),
            raw_content=v.raw_content,
            published_at=v.published_at
        )
        if saved:
            saved_count += 1
            print(f"   + Saved: [{v.source}] {v.title[:45]} (Content length: {len(v.raw_content)} chars)")
        else:
            duplicate_count += 1

    print(f"\n   Summary: {saved_count} newly saved, {duplicate_count} duplicates skipped.")
    
    print("\n4. Verifying total unprocessed items in database...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   [SUCCESS] Total items (RSS + YouTube) awaiting LLM summary: {len(unprocessed)}")

    print("\n[SUCCESS] Phase 3 YouTube Scraper test passed completely!")

if __name__ == "__main__":
    run_test()
