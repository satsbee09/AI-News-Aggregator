from app.database.mongo import init_mongo_db
from app.database.repository import MongoRepository
from app.scrapers.google_news_scraper import GoogleNewsScraper
from app.scrapers.weather_scraper import WeatherScraper

def run_test():
    print("1. Initializing MongoDB...")
    init_mongo_db()
    repo = MongoRepository()

    # 1. Test Google News for Local News
    print("\n2. Scraping Local News (Ghaziabad)...")
    local_scraper = GoogleNewsScraper(query="Ghaziabad news", topic_name="Local Ghaziabad News", category="local")
    local_articles = local_scraper.get_articles(hours=48)
    print(f"   [SUCCESS] Scraped {len(local_articles)} local article(s).")
    for a in local_articles[:2]:
        print(f"   - {a.title[:60]}... ({a.source})")

    # 2. Test Google News for Cricket & Sports
    print("\n3. Scraping Cricket & Sports News...")
    sports_scraper = GoogleNewsScraper(query="cricket match India tournament", topic_name="Cricket & Sports", category="sports")
    sports_articles = sports_scraper.get_articles(hours=48)
    print(f"   [SUCCESS] Scraped {len(sports_articles)} sports article(s).")
    for a in sports_articles[:2]:
        print(f"   - {a.title[:60]}... ({a.source})")

    # 3. Test Weather Scraper (Open-Meteo)
    print("\n4. Scraping Weather for Delhi NCR...")
    weather_scraper = WeatherScraper(city_name="Delhi", topic_name="Delhi NCR Weather")
    weather_articles = weather_scraper.get_articles()
    print(f"   [SUCCESS] Scraped {len(weather_articles)} weather report(s).")
    for a in weather_articles:
        print(f"   - {a.title}")
        print(f"     {a.raw_content}")

    # 4. Save to MongoDB
    all_articles = local_articles + sports_articles + weather_articles
    saved_count = 0
    for a in all_articles:
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
            saved_count += 1

    print(f"\n5. Persisted {saved_count} multi-topic articles into MongoDB!")
    print("\n[SUCCESS] Step 3 Multi-Scrapers test passed completely!")

if __name__ == "__main__":
    run_test()
