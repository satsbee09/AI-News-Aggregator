from typing import Optional
from app.database.repository import MongoRepository
from app.agent.digest_agent import DigestAgent

def process_unprocessed_digests(repo: Optional[MongoRepository] = None, limit: int = 10) -> int:
    """Fetches unprocessed raw articles from MongoDB and generates LLM summaries + vector embeddings."""
    repo = repo or MongoRepository()
    unprocessed_articles = repo.get_unprocessed_articles()

    if not unprocessed_articles:
        print("   [INFO] No unprocessed articles to summarize.")
        return 0

    to_process = unprocessed_articles[:limit]
    print(f"   Processing {len(to_process)} article(s) with Groq LLM...")

    agent = DigestAgent()
    processed_count = 0

    for article in to_process:
        source = article.get("source", "unknown")
        title = article.get("title", "Untitled")
        raw_content = article.get("raw_content", "")
        category = article.get("category", "general")
        topic_name = article.get("topic_name", "General News")
        article_id = article["_id"]

        safe_title = title.encode('ascii', 'replace').decode('ascii')[:45]
        print(f"   [AI] Summarizing [{source}]: {safe_title}...")
        try:
            # Special fast-path for weather reports
            if source == "open_meteo":
                summary = raw_content.split("\n")[0] if "\n" in raw_content else raw_content
                takeaways = "\n".join([f"- {line.strip()}" for line in raw_content.split("\n")[1:] if line.strip()])
                saved_digest = repo.save_digest(
                    article_id=article_id,
                    summary=summary,
                    key_takeaways=takeaways or "- Check local weather advisories",
                    category="weather",
                    topic_name=topic_name
                )
                processed_count += 1

                # Generate vector embedding
                try:
                    from app.services.embedding_service import embedding_service
                    embed_text = f"{title}\n{summary}\n{takeaways}"
                    vector = embedding_service.embed_text(embed_text)
                    repo.save_article_embedding(
                        article_id=article_id,
                        digest_id=saved_digest["_id"],
                        topic=topic_name,
                        title=title,
                        text=embed_text,
                        embedding=vector,
                        source_url=article.get("url", ""),
                        published_at=article.get("published_at")
                    )
                except Exception as emb_err:
                    print(f"      [WARN] Could not generate embedding for weather: {emb_err}")
                continue

            digest_data = agent.summarize(
                title=title,
                source=source,
                raw_content=raw_content
            )

            # Format takeaways as formatted markdown bullets
            formatted_takeaways = "\n".join([f"- {bullet.lstrip('•-* ')}" for bullet in digest_data.key_takeaways])

            saved_digest = repo.save_digest(
                article_id=article_id,
                summary=digest_data.summary,
                key_takeaways=formatted_takeaways,
                category=category if category != "general" else digest_data.category.lower(),
                topic_name=topic_name
            )
            processed_count += 1

            # Generate and persist vector embedding in article_embeddings
            try:
                from app.services.embedding_service import embedding_service
                embed_text = f"{title}\n{digest_data.summary}\n{formatted_takeaways}"
                vector = embedding_service.embed_text(embed_text)
                repo.save_article_embedding(
                    article_id=article_id,
                    digest_id=saved_digest["_id"],
                    topic=topic_name,
                    title=title,
                    text=embed_text,
                    embedding=vector,
                    source_url=article.get("url", ""),
                    published_at=article.get("published_at")
                )
            except Exception as emb_err:
                print(f"      [WARN] Could not generate embedding for article ID={article_id}: {emb_err}")

        except Exception as e:
            print(f"   [ERROR] Failed to summarize article ID={article_id}: {e}")

    print(f"   [SUCCESS] Successfully generated {processed_count} digest(s).")
    return processed_count
