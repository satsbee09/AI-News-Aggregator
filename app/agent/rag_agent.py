import logging
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from app.database.repository import MongoRepository
from app.services.embedding_service import embedding_service
from app.services.search_service import search_service
from app.agent.base_llm import LLMClient

logger = logging.getLogger(__name__)

# Cosine similarity threshold for stored vector sufficiency
SIMILARITY_THRESHOLD = 0.70

class RAGState(TypedDict):
    question: str
    email: Optional[str]
    topics: Optional[List[str]]
    retrieved_articles: List[Dict[str, Any]]
    live_articles: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    from_live_search: bool
    grounded: bool
    answer: str

class RAGAgent:
    def __init__(self, repo: Optional[MongoRepository] = None):
        self.repo = repo or MongoRepository()
        self.llm = LLMClient()
        self.graph = self._build_graph()

    def _vector_search_node(self, state: RAGState) -> Dict[str, Any]:
        """Node 1: Vector similarity retrieval against MongoDB Atlas."""
        question = state.get("question", "").strip()
        email = state.get("email")
        user_topics = state.get("topics")

        # Resolve user topics if not passed
        if not user_topics and email:
            user_doc = self.repo.db.users.find_one({"email": email.lower().strip()})
            if user_doc and "topics" in user_doc:
                user_topics = [t.get("name") for t in user_doc["topics"] if t.get("name")]

        if not question:
            return {"retrieved_articles": [], "topics": user_topics}

        # Embed question
        query_vector = embedding_service.embed_text(question)

        # Scoped vector search
        articles = self.repo.vector_search(
            query_vector=query_vector,
            limit=6,
            topics=user_topics if (user_topics and len(user_topics) > 0) else None
        )

        # Fallback to general vector search if no matches in selected topics
        if not articles:
            articles = self.repo.vector_search(query_vector=query_vector, limit=6, topics=None)

        return {"retrieved_articles": articles, "topics": user_topics}

    def _check_retrieval_condition(self, state: RAGState) -> str:
        """Conditional Edge: Determines if vector results are sufficient or fallback to live search."""
        articles = state.get("retrieved_articles", [])
        if not articles or len(articles) == 0:
            logger.info("[RAG GRAPH] No vector matches found. Routing to live web search fallback.")
            return "live_search"

        top_score = float(articles[0].get("score", 0.0))
        if top_score < SIMILARITY_THRESHOLD:
            logger.info(f"[RAG GRAPH] Vector similarity ({top_score:.3f}) < threshold ({SIMILARITY_THRESHOLD}). Routing to live search.")
            return "live_search"

        logger.info(f"[RAG GRAPH] Vector similarity ({top_score:.3f}) >= threshold ({SIMILARITY_THRESHOLD}). Routing to direct synthesis.")
        return "synthesize"

    def _live_search_node(self, state: RAGState) -> Dict[str, Any]:
        """Node 2: Live web search fallback via Google CSE / Brave Search."""
        question = state.get("question", "")
        topics = state.get("topics", [])
        primary_topic = topics[0] if (topics and len(topics) > 0) else None

        logger.info(f"[RAG GRAPH] Executing live web search for: '{question}' (topic: {primary_topic})")
        live_results = search_service.live_search(query=question, topic=primary_topic, num_results=6)
        
        return {
            "live_articles": live_results,
            "from_live_search": True
        }

    def _synthesize_answer_node(self, state: RAGState) -> Dict[str, Any]:
        """Node 3: Grounded response synthesis and citation generation with Groq LLM."""
        question = state.get("question", "")
        from_live = state.get("from_live_search", False)
        
        context_blocks = []
        sources_meta = []

        if from_live:
            # Format live web search context
            live_items = state.get("live_articles", [])
            for idx, item in enumerate(live_items, start=1):
                title = item.get("title", "Untitled")
                snippet = item.get("snippet", "")
                url = item.get("url", "#")
                src = item.get("source", "web").capitalize()

                context_blocks.append(f"[Live Source #{idx}]\nTitle: {title}\nProvider: {src}\nDetails: {snippet}\n")
                sources_meta.append({
                    "title": title,
                    "url": url,
                    "source": f"Live Web ({src})",
                    "date": "Live Today",
                    "score": None
                })
        else:
            # Format stored vector context
            stored_items = state.get("retrieved_articles", [])
            for idx, item in enumerate(stored_items, start=1):
                title = item.get("title", "Untitled Article")
                text = item.get("text", "")
                topic = item.get("topic", "News")
                source_url = item.get("source_url", "")
                pub_date = item.get("published_at")
                
                date_str = pub_date.strftime("%B %d, %Y") if isinstance(pub_date, datetime) else "Recent"
                score = round(float(item.get("score", 0.0)), 3)

                context_blocks.append(f"[Stored Source #{idx}]\nTitle: {title}\nTopic: {topic}\nPublished: {date_str}\nContent:\n{text[:600]}\n")
                sources_meta.append({
                    "title": title,
                    "url": source_url or "#",
                    "source": topic,
                    "date": date_str,
                    "score": score
                })

        if not context_blocks:
            return {
                "answer": "I could not find enough relevant information from either your news collection or live web search to answer this question.",
                "sources": [],
                "grounded": False
            }

        context_str = "\n---\n".join(context_blocks)
        
        system_prompt = """You are an elite, articulate AI News Intelligence Assistant.
Your objective is to answer the user's question accurately, concisely, and insightfully based ONLY on the provided news articles below.

Rules:
1. Ground every statement in the provided sources. Do not make assumptions or extrapolate beyond the provided text.
2. Naturally cite which source or publication each key fact comes from (e.g. "According to...", "As reported in...").
3. If the provided articles do not contain sufficient details to fully answer, state what is known and note what is missing.
4. Format your answer cleanly with readable paragraphs and bullet points where helpful."""

        user_prompt = f"""Retrieved News Context:
{context_str}

User Question:
{question}

Please provide your grounded answer with citations now:"""

        try:
            answer = self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, json_mode=False)
        except Exception as e:
            logger.error(f"[RAG GRAPH ERROR] LLM generation failed: {e}")
            top_title = sources_meta[0]["title"] if sources_meta else "Recent Stories"
            answer = f"Based on recent news matches for '{top_title}', relevant coverage was identified.\n\n(Generated via fallback synthesis)"

        return {
            "answer": answer.strip(),
            "sources": sources_meta,
            "grounded": True
        }

    def _build_graph(self):
        """Builds and compiles the LangGraph state machine."""
        workflow = StateGraph(RAGState)

        # Add Nodes
        workflow.add_node("vector_search", self._vector_search_node)
        workflow.add_node("live_search", self._live_search_node)
        workflow.add_node("synthesize", self._synthesize_answer_node)

        # Set Entry Point
        workflow.set_entry_point("vector_search")

        # Add Conditional Edge from vector_search
        workflow.add_conditional_edges(
            "vector_search",
            self._check_retrieval_condition,
            {
                "synthesize": "synthesize",
                "live_search": "live_search"
            }
        )

        # Add Edge from live_search to synthesize
        workflow.add_edge("live_search", "synthesize")

        # Add Edge from synthesize to END
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def answer_question(
        self,
        email: str,
        question: str,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the LangGraph RAG workflow and returns grounded answer, sources, and provenance.
        """
        cleaned_question = question.strip()
        if not cleaned_question:
            return {
                "answer": "Please ask a question about the latest news.",
                "sources": [],
                "from_live_search": False,
                "grounded": False
            }

        initial_state: RAGState = {
            "question": cleaned_question,
            "email": email,
            "topics": topics,
            "retrieved_articles": [],
            "live_articles": [],
            "sources": [],
            "from_live_search": False,
            "grounded": False,
            "answer": ""
        }

        # Invoke compiled LangGraph
        result = self.graph.invoke(initial_state)

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "from_live_search": result.get("from_live_search", False),
            "grounded": result.get("grounded", True)
        }

rag_agent = RAGAgent()
