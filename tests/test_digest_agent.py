from app.database.mongo import init_mongo_db
from app.database.repository import MongoRepository
from app.services.process_digest import process_unprocessed_digests

def run_test():
    print("1. Initializing MongoDB...")
    init_mongo_db()
    repo = MongoRepository()

    print("\n2. Checking unprocessed articles in MongoDB...")
    unprocessed = repo.get_unprocessed_articles()
    print(f"   Found {len(unprocessed)} unprocessed article(s).")
    
    if len(unprocessed) == 0:
        print("   [INFO] No raw unprocessed articles. Creating a quick mock raw article for testing...")
        repo.save_article(
            title="DeepSeek-R1 Architecture and Reasoning Insights",
            url="https://arxiv.org/abs/2501.12948_test",
            source="arxiv",
            category="ai",
            topic_name="Frontier AI & LLMs",
            raw_content="DeepSeek-R1 introduces pure reinforcement learning training for complex reasoning tasks without supervised fine-tuning warm-start."
        )
        unprocessed = repo.get_unprocessed_articles()

    assert len(unprocessed) > 0, "No raw articles found."

    print("\n3. Running Groq LLM Summarizer on top 3 articles...")
    processed_count = process_unprocessed_digests(repo=repo, limit=3)
    assert processed_count > 0, "Failed: No digests were processed."

    print("\n4. Inspecting newly generated digests in database:")
    unsent_digests = repo.get_unsent_digests()
    for d in unsent_digests[:3]:
        article = d.get("article", {})
        category = d.get("category", "general")
        title = article.get("title", "Untitled")
        source = article.get("source", "unknown")
        url = article.get("url", "")
        summary = d.get("summary", "")
        takeaways = d.get("key_takeaways", "")

        print("\n" + "="*60)
        print(f"[{category.upper()}] Article: {title}")
        print(f"Source: {source} | URL: {url}")
        print(f"\nSUMMARY:\n{summary}")
        print(f"\nKEY TAKEAWAYS:\n{takeaways}")
        print("="*60)

    print("\n[SUCCESS] Phase 4 LLM Summarizer test passed completely!")

if __name__ == "__main__":
    run_test()
