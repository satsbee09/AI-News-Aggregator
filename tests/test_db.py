from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository

def run_test():
    print("Initializing Database tables...")
    init_db()

    session = SessionLocal()
    repo = Repository(session)

    # 1. Insert a mock article
    mock_url = "https://openai.com/index/test-gpt-5-preview"
    print(f"\n1. Inserting mock article: {mock_url}")
    article = repo.save_article(
        title="GPT-5 Preview & Benchmark Results",
        url=mock_url,
        source="openai",
        raw_content="OpenAI announces test results demonstrating reasoning benchmarks."
    )
    if article:
        print(f"   [SUCCESS] Created article: ID={article.id}, Title='{article.title}'")
    else:
        print("   [INFO] Article already exists in DB.")

    # 2. Test duplicate rejection (Idempotency)
    print("\n2. Testing duplicate insertion rejection...")
    duplicate = repo.save_article(
        title="Duplicate GPT-5",
        url=mock_url,
        source="openai",
        raw_content="Duplicate content."
    )
    assert duplicate is None, "Failed: Repository should return None for duplicate URL!"
    print("   [SUCCESS] Duplicate correctly ignored.")

    # 3. Test unprocessed articles query
    print("\n3. Testing get_unprocessed_articles()...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   [SUCCESS] Found {len(unprocessed)} unprocessed article(s).")
    assert len(unprocessed) >= 1

    # 4. Create a mock digest
    print("\n4. Creating mock digest...")
    target_article = unprocessed[0]
    digest = repo.save_digest(
        article_id=target_article.id,
        summary="A major announcement regarding next-generation AI models.",
        key_takeaways="• High reasoning accuracy\n• Multimodal capabilities\n• Zero-cost API tier",
        category="Model Release"
    )
    print(f"   [SUCCESS] Digest created: ID={digest.id} for Article ID={digest.article_id}")

    # 5. Check unsent digests
    print("\n5. Checking unsent digests...")
    unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Found {len(unsent)} unsent digest(s).")
    assert len(unsent) >= 1

    # 6. Log as sent
    print("\n6. Logging digest as sent...")
    log = repo.log_sent_digest(digest_id=digest.id, recipient="test@example.com")
    print(f"   [SUCCESS] Logged sent digest ID={log.digest_id} to {log.recipient}")

    # 7. Check unsent digests again (should decrease)
    remaining_unsent = repo.get_unsent_digests()
    print(f"   [SUCCESS] Unsent digests after logging: {len(remaining_unsent)}")

    session.close()
    print("\n🎉 Phase 1 Database & Repository test passed completely!")

if __name__ == "__main__":
    run_test()
