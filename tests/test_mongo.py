from app.database.mongo import init_mongo_db, get_mongo_db
from app.database.repository import MongoRepository

def run_test():
    print("1. Initializing MongoDB and creating collections/indexes...")
    init_mongo_db()
    repo = MongoRepository()

    # Check active topics
    topics = repo.get_active_topics()
    print(f"\n2. Loaded {len(topics)} active user topics from MongoDB:")
    for t in topics:
        print(f"   - [{t['category'].upper()}] {t['topic_name']} (Weight: {t.get('weight', 1.0)})")

    # Insert mock article
    mock_url = "https://example.com/mongo-test-article-1"
    print(f"\n3. Inserting mock article: {mock_url}")
    article = repo.save_article(
        title="MongoDB Multi-Topic Test Article",
        url=mock_url,
        source="test_source",
        category="national",
        topic_name="National News & Politics",
        raw_content="Testing MongoDB insertion and deduplication."
    )
    if article:
        print(f"   [SUCCESS] Created article in Mongo with _id: {article['_id']}")

    # Test duplicate prevention
    print("\n4. Testing duplicate URL rejection...")
    duplicate = repo.save_article(
        title="Duplicate",
        url=mock_url,
        source="test_source",
        category="national",
        topic_name="National News & Politics",
        raw_content="Duplicate content."
    )
    assert duplicate is None, "Failed: MongoDB unique index should reject duplicate URL!"
    print("   [SUCCESS] Duplicate correctly ignored.")

    # Create mock digest
    print("\n5. Creating mock digest in MongoDB...")
    digest = repo.save_digest(
        article_id=article["_id"],
        summary="Summary of MongoDB article.",
        key_takeaways="- Takeaway 1\n- Takeaway 2",
        category="national",
        topic_name="National News & Politics"
    )
    print(f"   [SUCCESS] Created digest with _id: {digest['_id']}")

    # Check unsent digests
    print("\n6. Checking unsent digests with $lookup join...")
    unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Found {len(unsent)} unsent digest(s).")
    assert len(unsent) >= 1

    # Log as sent
    print("\n7. Logging digest as sent in MongoDB...")
    repo.log_sent_digest(digest_id=digest["_id"], recipient="test@example.com")
    remaining_unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Remaining unsent digests: {len(remaining_unsent)}")

    print("\n[SUCCESS] MongoDB Migration test passed completely!")

if __name__ == "__main__":
    run_test()
