from app.database.mongo import init_mongo_db
from app.database.repository import MongoRepository

def run_test():
    print("1. Initializing MongoDB Atlas collections and indexes...")
    init_mongo_db()
    repo = MongoRepository()

    # 1. Insert a mock article
    mock_url = "https://openai.com/index/test-gpt-5-preview"
    print(f"\n2. Inserting mock article: {mock_url}")
    article = repo.save_article(
        title="GPT-5 Preview & Benchmark Results",
        url=mock_url,
        source="openai",
        category="ai",
        topic_name="Frontier AI & LLMs",
        raw_content="OpenAI announces test results demonstrating reasoning benchmarks."
    )
    if article:
        print(f"   [SUCCESS] Created article: ID={article['_id']}, Title='{article['title']}'")
    else:
        print("   [INFO] Article already exists in DB.")

    # 2. Test duplicate rejection (Idempotency via unique URL index)
    print("\n3. Testing duplicate insertion rejection...")
    duplicate = repo.save_article(
        title="Duplicate GPT-5",
        url=mock_url,
        source="openai",
        category="ai",
        topic_name="Frontier AI & LLMs",
        raw_content="Duplicate content."
    )
    assert duplicate is None, "Failed: Repository should return None for duplicate URL!"
    print("   [SUCCESS] Duplicate correctly ignored.")

    # 3. Test unprocessed articles query
    print("\n4. Testing get_unprocessed_articles()...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   [SUCCESS] Found {len(unprocessed)} unprocessed article(s).")
    assert len(unprocessed) >= 1

    # 4. Create a mock digest
    print("\n5. Creating mock digest...")
    target_article = unprocessed[0]
    digest = repo.save_digest(
        article_id=target_article["_id"],
        summary="A major announcement regarding next-generation AI models.",
        key_takeaways="• High reasoning accuracy\n• Multimodal capabilities\n• Zero-cost API tier",
        category="ai",
        topic_name="Frontier AI & LLMs"
    )
    print(f"   [SUCCESS] Digest created: ID={digest['_id']} for Article ID={digest['article_id']}")

    # 5. Check unsent digests with MongoDB $lookup join
    print("\n6. Checking unsent digests...")
    unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Found {len(unsent)} unsent digest(s).")
    assert len(unsent) >= 1

    # 6. Log as sent
    print("\n7. Logging digest as sent...")
    log = repo.log_sent_digest(digest_id=digest["_id"], recipient="test@example.com")
    print(f"   [SUCCESS] Logged sent digest ID={log['digest_id']} to {log['recipient']}")

    # 7. Check unsent digests again (should decrease)
    remaining_unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Unsent digests after logging: {len(remaining_unsent)}")

    print("\n[SUCCESS] MongoDB Database & Repository test passed completely!")

if __name__ == "__main__":
    run_test()
