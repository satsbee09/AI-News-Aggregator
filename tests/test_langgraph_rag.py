import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient
from app.server import app
from app.config import settings
from app.agent.rag_agent import RAGAgent

client = TestClient(app)
SECRET_HEADER = {"X-Internal-Secret": settings.INTERNAL_API_SECRET}

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    return repo

def test_langgraph_rag_vector_path():
    """Test when vector similarity score is high, it routes to direct vector synthesis."""
    mock_repo = MagicMock()
    mock_repo.vector_search.return_value = [
        {
            "title": "Frontier AI Released",
            "text": "A new generative model with 100B params was open sourced.",
            "topic": "ai",
            "source_url": "https://example.com/ai",
            "published_at": None,
            "score": 0.88
        }
    ]

    with patch("app.agent.rag_agent.LLMClient.generate", return_value="The frontier model has 100B parameters."):
        agent = RAGAgent(repo=mock_repo)
        result = agent.answer_question(email="test@example.com", question="What AI models were released?")
        
        assert result["from_live_search"] is False
        assert result["grounded"] is True
        assert len(result["sources"]) == 1
        assert "100B parameters" in result["answer"]

def test_langgraph_rag_live_search_fallback_path():
    """Test when vector search has no matches or low score, it routes to live search fallback."""
    mock_repo = MagicMock()
    mock_repo.vector_search.return_value = []  # No stored vector matches

    mock_live_results = [
        {
            "title": "NASA Launches Artemis Mission",
            "url": "https://example.com/artemis",
            "snippet": "NASA rocket lifted off towards the lunar orbit successfully.",
            "source": "google"
        }
    ]

    with patch("app.services.search_service.search_service.live_search", return_value=mock_live_results), \
         patch("app.agent.rag_agent.LLMClient.generate", return_value="NASA launched the Artemis mission successfully."):
        
        agent = RAGAgent(repo=mock_repo)
        result = agent.answer_question(email="test@example.com", question="Did NASA launch Artemis?")
        
        assert result["from_live_search"] is True
        assert result["grounded"] is True
        assert len(result["sources"]) == 1
        assert result["sources"][0]["source"] == "Live Web (Google)"
        assert "Artemis" in result["answer"]

def test_internal_ask_endpoint_passes_from_live_search():
    """Test that POST /internal/ask returns from_live_search boolean."""
    with patch("app.agent.rag_agent.rag_agent.answer_question", return_value={
        "answer": "Grounded answer from live search.",
        "sources": [{"title": "Live News", "url": "https://example.com", "source": "Live Web (Google)"}],
        "from_live_search": True,
        "grounded": True
    }):
        res = client.post(
            "/internal/ask",
            headers=SECRET_HEADER,
            json={"email": "test@example.com", "question": "Latest space news?"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["from_live_search"] is True
        assert data["grounded"] is True
        assert data["answer"] == "Grounded answer from live search."
