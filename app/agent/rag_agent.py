from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.repository import MongoRepository
from app.services.embedding_service import embedding_service
from app.agent.base_llm import LLMClient

class RAGAgent:
    def __init__(self, repo: Optional[MongoRepository] = None):
        self.repo = repo or MongoRepository()
        self.llm = LLMClient()

    def answer_question(
        self,
        email: str,
        question: str,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Embeds question, performs vector retrieval scoped to user topics,
        and generates a grounded answer with citations using Groq LLM.
        """
        cleaned_question = question.strip()
        if not cleaned_question:
            return {
                "answer": "Please ask a question about the latest news.",
                "sources": []
            }

        # 1. Resolve user's topics if not passed explicitly
        user_topics = topics
        if not user_topics and email:
            user_doc = self.repo.db.users.find_one({"email": email.lower().strip()})
            if user_doc and "topics" in user_doc:
                user_topics = [t.get("name") for t in user_doc["topics"] if t.get("name")]

        # 2. Embed the natural language question
        query_vector = embedding_service.embed_text(cleaned_question)

        # 3. Vector similarity retrieval against article_embeddings
        retrieved_articles = self.repo.vector_search(
            query_vector=query_vector,
            limit=6,
            topics=user_topics if (user_topics and len(user_topics) > 0) else None
        )

        # Fallback to general vector search if no results within user topic scope
        if not retrieved_articles:
            retrieved_articles = self.repo.vector_search(query_vector=query_vector, limit=6, topics=None)

        if not retrieved_articles:
            return {
                "answer": "I couldn't find any relevant news articles in your collection to answer that question. Try selecting more topics or checking back once new digests are processed.",
                "sources": []
            }

        # 4. Construct grounded context prompt
        context_blocks = []
        sources_meta = []

        for idx, item in enumerate(retrieved_articles, start=1):
            title = item.get("title", "Untitled Article")
            text = item.get("text", "")
            topic = item.get("topic", "News")
            source_url = item.get("source_url", "")
            pub_date = item.get("published_at")
            
            date_str = pub_date.strftime("%B %d, %Y") if isinstance(pub_date, datetime) else "Recent"
            score = round(float(item.get("score", 0.0)), 3)

            context_blocks.append(f"""[Source #{idx}]
Title: {title}
Topic: {topic}
Published: {date_str}
Content:
{text[:600]}
""")

            sources_meta.append({
                "title": title,
                "url": source_url or "#",
                "source": topic,
                "date": date_str,
                "score": score
            })

        context_str = "\n---\n".join(context_blocks)

        system_prompt = """You are an elite, articulate AI News Intelligence Assistant.
Your objective is to answer the user's question accurately, concisely, and insightfully based ONLY on the provided news articles below.

Rules:
1. Ground every statement in the provided sources. Do not make assumptions or extrapolate beyond the provided text.
2. Naturally cite which source or publication each key fact comes from (e.g. "According to...", "As reported in...").
3. If the provided articles do not contain sufficient details to fully answer, state what is known from the articles and note what is missing.
4. Format your answer cleanly with readable paragraphs and bullet points where helpful."""

        user_prompt = f"""Retrieved News Context:
{context_str}

User Question:
{cleaned_question}

Please provide your grounded answer with citations now:"""

        try:
            answer = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=False)
        except Exception as e:
            print(f"[RAG AGENT ERROR] LLM generation failed: {e}")
            # Resilient fallback summary based on top retrieved sources
            top_snippet = retrieved_articles[0].get("text", "")[:250]
            answer = f"Based on the most relevant match ('{retrieved_articles[0].get('title')}'):\n\n{top_snippet}...\n\n(Generated via local retrieval fallback)"

        return {
            "answer": answer.strip(),
            "sources": sources_meta
        }

rag_agent = RAGAgent()
