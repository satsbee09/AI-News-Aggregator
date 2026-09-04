import pytest
from app.services.embedding_service import embedding_service
from app.database.repository import MongoRepository

def test_embedding_dimensions_and_similarity():
    """Verify that FastEmbed produces 384-dimensional vectors and cosine similarity works."""
    text1 = "OpenAI releases new GPT-5 model with enhanced reasoning capabilities."
    text2 = "Artificial intelligence LLMs and reasoning neural networks."
    text3 = "Cricket tournament results: India beats Australia in World Cup final."

    v1 = embedding_service.embed_text(text1)
    v2 = embedding_service.embed_text(text2)
    v3 = embedding_service.embed_text(text3)

    assert len(v1) == 384, f"Expected 384 dimensions, got {len(v1)}"
    assert len(v2) == 384
    assert len(v3) == 384

    sim_ai = embedding_service.cosine_similarity(v1, v2)
    sim_cross = embedding_service.cosine_similarity(v1, v3)

    print(f"\n[TEST] AI-to-AI similarity: {sim_ai:.4f}")
    print(f"[TEST] AI-to-Cricket similarity: {sim_cross:.4f}")

    assert sim_ai > sim_cross, f"Expected AI-to-AI similarity ({sim_ai}) > AI-to-Cricket ({sim_cross})"
    assert sim_ai > 0.5, "Expected high semantic similarity for related topics"

def test_mongodb_vector_search_retrieval():
    """Verify vector search against stored article_embeddings collection in MongoDB."""
    repo = MongoRepository()
    total_embeddings = repo.db.article_embeddings.count_documents({})
    assert total_embeddings > 0, "Expected at least 1 document in article_embeddings"

    # Query 1: Search for sports/cricket
    query_text = "cricket match series score and tournament update"
    query_vec = embedding_service.embed_text(query_text)

    results = repo.vector_search(query_vec, limit=5)
    assert len(results) > 0, "Expected vector search results"

    for r in results:
        title = r.get("title", "")[:60]
        topic = r.get("topic", "General")
        score = r.get("score", 0.0)
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"   [{topic}] (Score: {score:.4f}) {safe_title}")

    # Verify that results have title, text, embedding/score
    top_result = results[0]
    assert "title" in top_result
    assert "text" in top_result

def test_mongodb_vector_search_topic_filter():
    """Verify that topic filtering scopes vector search results."""
    repo = MongoRepository()
    query_text = "latest updates and breakthroughs"
    query_vec = embedding_service.embed_text(query_text)

    # Get distinct topics available
    all_topics = repo.db.article_embeddings.distinct("topic")
    if all_topics:
        target_topic = all_topics[0]
        scoped_results = repo.vector_search(query_vec, limit=4, topics=[target_topic])
        print(f"\n[TEST] Scoped results for topic '{target_topic}': {len(scoped_results)}")
        for r in scoped_results:
            assert r.get("topic") == target_topic, f"Expected topic {target_topic}, got {r.get('topic')}"
