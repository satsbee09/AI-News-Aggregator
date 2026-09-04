from sqlalchemy.orm import Session
from app.database.repository import Repository
from app.agent.digest_agent import DigestAgent

def process_unprocessed_digests(session: Session, limit: int = 5) -> int:
    """Fetches unprocessed raw articles and generates LLM summaries."""
    repo = Repository(session)
    unprocessed_articles = repo.get_unprocessed_articles()

    if not unprocessed_articles:
        print("   [INFO] No unprocessed articles to summarize.")
        return 0

    to_process = unprocessed_articles[:limit]
    print(f"   Processing {len(to_process)} article(s) with Groq LLaMA 3.3...")

    agent = DigestAgent()
    processed_count = 0

    for article in to_process:
        print(f"   [AI] Summarizing [{article.source}]: {article.title[:45]}...")
        try:
            digest_data = agent.summarize(
                title=article.title,
                source=article.source,
                raw_content=article.raw_content
            )

            # Format takeaways as formatted markdown bullets
            formatted_takeaways = "\n".join([f"- {bullet.lstrip('•-* ')}" for bullet in digest_data.key_takeaways])

            repo.save_digest(
                article_id=article.id,
                summary=digest_data.summary,
                key_takeaways=formatted_takeaways,
                category=digest_data.category
            )
            processed_count += 1
        except Exception as e:
            print(f"   [ERROR] Failed to summarize article ID={article.id}: {e}")

    print(f"   [SUCCESS] Successfully generated {processed_count} digest(s).")
    return processed_count
