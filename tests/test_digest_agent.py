from app.database.connection import init_db, SessionLocal
from app.database.repository import Repository
from app.services.process_digest import process_unprocessed_digests

def run_test():
    print("1. Initializing Database...")
    init_db()
    session = SessionLocal()
    repo = Repository(session)

    print("\n2. Checking unprocessed articles in DB...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   Found {len(unprocessed)} unprocessed article(s).")
    assert len(unprocessed) > 0, "No raw articles found. Run Phase 2 or 3 tests first!"

    print("\n3. Running LLM Summarizer on top 3 articles...")
    processed_count = process_unprocessed_digests(session, limit=3)
    assert processed_count > 0, "Failed: No digests were processed."

    print("\n4. Inspecting newly generated digests in database:")
    unsent_digests = repo.get_unsent_digests()
    for d in unsent_digests[:3]:
        print("\n" + "="*60)
        print(f"[{d.category.upper()}] Article: {d.article.title}")
        print(f"Source: {d.article.source} | URL: {d.article.url}")
        print(f"\nSUMMARY:\n{d.summary}")
        print(f"\nKEY TAKEAWAYS:\n{d.key_takeaways}")
        print("="*60)

    session.close()
    print("\n[SUCCESS] Phase 4 LLM Summarizer test passed completely!")

if __name__ == "__main__":
    run_test()
