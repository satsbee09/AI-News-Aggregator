import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from app.server import app
from app.config import settings

client = TestClient(app)
SECRET_HEADER = {"X-Internal-Secret": settings.INTERNAL_API_SECRET}

def test_internal_live_search_rejects_unauthorized():
    res = client.post("/internal/search-live", json={"query": "AI breakthroughs"})
    assert res.status_code == 401

def test_internal_live_search_success():
    mock_results = [
        {
            "title": "Quantum Computing Milestone Reached",
            "url": "https://example.com/quantum",
            "snippet": "Researchers announce 1,000 qubit operational milestone.",
            "source": "google",
            "published": "2026-09-04T12:00:00Z"
        }
    ]

    with patch("app.services.search_service.search_service.live_search", return_value=mock_results):
        res = client.post(
            "/internal/search-live",
            headers=SECRET_HEADER,
            json={"query": "Quantum computing", "topic": "ai"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["query"] == "Quantum computing"
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Quantum Computing Milestone Reached"
        assert data["results"][0]["source"] == "google"
