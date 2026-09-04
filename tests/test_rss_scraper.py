from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository
from app.scrapers.rss_scraper import RssScraper

def run_test():
    print("1. Initializing Database...")
    init_db()
    session = SessionLocal()
    repo = Repository(session)

    print("\n2. Fetching recent AI RSS articles (last 72 hours)...")
    scraper = RssScraper()
    articles = scraper.get_articles(hours=72)
    print(f"   [SUCCESS] Scraped {len(articles)} article(s) from live feeds.")

    # If no articles within 72 hours, fallback to latest 5 items without time filter
    if not articles:
        print("   [INFO] No articles in last 72 hours. Fetching latest available...")
        articles = scraper.get_articles(hours=0)[:5]
        print(f"   [SUCCESS] Scraped {len(articles)} latest article(s).")

    assert len(articles) > 0, "Failed: Could not scrape any articles from RSS feeds."

    print("\n3. Saving scraped articles to SQLite database...")
    saved_count = 0
    duplicate_count = 0
    for a in articles:
        saved = repo.save_article(
            title=a.title,
            url=a.url,
            source=a.source,
            raw_content=a.raw_content,
            published_at=a.published_at
        )
        if saved:
            saved_count += 1
            print(f"   + Saved: [{a.source.upper()}] {a.title[:45]}...")
        else:
            duplicate_count += 1

    print(f"\n   Summary: {saved_count} newly saved, {duplicate_count} duplicates skipped.")
    
    print("\n4. Verifying unprocessed articles count...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   [SUCCESS] Total unprocessed articles awaiting LLM summary: {len(unprocessed)}")

    session.close()
    print("\n🎉 Phase 2 RSS Scraper test passed completely!")

if __name__ == "__main__":
    run_test()
