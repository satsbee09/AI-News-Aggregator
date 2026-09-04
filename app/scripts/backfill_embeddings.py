import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from app.database.repository import MongoRepository
from app.services.embedding_service import embedding_service

def backfill_embeddings():
    print("=================================================================")
    print("--- STARTING VECTOR EMBEDDINGS BACKFILL FOR HISTORICAL NEWS ---")
    print("=================================================================")

    start_time = time.time()
    repo = MongoRepository()

    # 1. Fetch unembedded digests
    unembedded = repo.get_unembedded_digests()
    total_unembedded = len(unembedded)
    print(f"Found {total_unembedded} historical digest(s) lacking vector embeddings.")

    if total_unembedded == 0:
        print("[SUCCESS] All historical digests are already embedded!")
        total_embedded = repo.db.article_embeddings.count_documents({})
        print(f"Total vector embeddings in 'article_embeddings' collection: {total_embedded}")
        return

    # 2. Batch process embeddings
    print("Generating 384-dimensional embeddings in batches...")
    batch_size = 32
    processed_count = 0

    for i in range(0, total_unembedded, batch_size):
        batch = unembedded[i:i + batch_size]
        texts = []
        metadata_list = []

        for d in batch:
            digest_id = d["_id"]
            article = d.get("article", {})
            title = article.get("title", d.get("topic_name", "Untitled News"))
            summary = d.get("summary", "")
            takeaways = d.get("key_takeaways", "")
            topic = d.get("topic_name", "General News")
            source_url = article.get("url", "")
            published_at = article.get("published_at")
            article_id = d.get("article_id")

            embed_text = f"{title}\n{summary}\n{takeaways}"
            texts.append(embed_text)
            metadata_list.append({
                "article_id": article_id,
                "digest_id": digest_id,
                "topic": topic,
                "title": title,
                "text": embed_text,
                "source_url": source_url,
                "published_at": published_at
            })

        vectors = embedding_service.embed_batch(texts)

        for meta, vector in zip(metadata_list, vectors):
            repo.save_article_embedding(
                article_id=meta["article_id"],
                digest_id=meta["digest_id"],
                topic=meta["topic"],
                title=meta["title"],
                text=meta["text"],
                embedding=vector,
                source_url=meta["source_url"],
                published_at=meta["published_at"]
            )
            processed_count += 1

        print(f"   Indexed {processed_count}/{total_unembedded} embeddings...")

    elapsed = round(time.time() - start_time, 2)
    total_in_db = repo.db.article_embeddings.count_documents({})
    print("=================================================================")
    print(f"[SUCCESS] BACKFILL COMPLETED in {elapsed}s!")
    print(f"Total vector embeddings stored in 'article_embeddings': {total_in_db}")
    print("=================================================================")

if __name__ == "__main__":
    backfill_embeddings()
