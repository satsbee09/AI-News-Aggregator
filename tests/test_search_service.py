import pytest
from unittest.mock import patch, MagicMock
from app.services.search_service import SearchService

@pytest.fixture
def mock_search_service():
    service = SearchService()
    service.google_api_key = "test_google_key"
    service.google_cse_id = "test_google_cx"
    service.brave_api_key = "test_brave_key"
    return service

def test_google_search_success(mock_search_service):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "title": "OpenAI Unveils New Model",
                "link": "https://example.com/openai",
                "snippet": "OpenAI announced its latest frontier model today."
            }
        ]
    }

    with patch("requests.get", return_value=mock_response):
        results = mock_search_service.google_search("OpenAI news")
        assert len(results) == 1
        assert results[0]["title"] == "OpenAI Unveils New Model"
        assert results[0]["url"] == "https://example.com/openai"
        assert results[0]["source"] == "google"
        assert mock_search_service.google_query_count == 1

def test_brave_search_success(mock_search_service):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {
                    "title": "Brave AI Search Result",
                    "url": "https://example.com/brave",
                    "description": "Brave search returns quick summary."
                }
            ]
        }
    }

    with patch("requests.get", return_value=mock_response):
        results = mock_search_service.brave_search("AI developments")
        assert len(results) == 1
        assert results[0]["title"] == "Brave AI Search Result"
        assert results[0]["url"] == "https://example.com/brave"
        assert results[0]["source"] == "brave"

def test_live_search_fallback_to_brave_on_google_429(mock_search_service):
    # Google returns 429
    google_mock_resp = MagicMock()
    google_mock_resp.ok = False
    google_mock_resp.status_code = 429

    # Brave returns 200
    brave_mock_resp = MagicMock()
    brave_mock_resp.ok = True
    brave_mock_resp.status_code = 200
    brave_mock_resp.json.return_value = {
        "web": {
            "results": [
                {
                    "title": "Brave Fallback Result",
                    "url": "https://example.com/fallback",
                    "description": "Retrieved via Brave fallback."
                }
            ]
        }
    }

    def mock_requests_get(url, **kwargs):
        if "googleapis.com" in url:
            return google_mock_resp
        elif "brave.com" in url:
            return brave_mock_resp
        return MagicMock(ok=False, status_code=500)

    with patch("requests.get", side_effect=mock_requests_get):
        results = mock_search_service.live_search("Latest weather updates")
        assert len(results) == 1
        assert results[0]["title"] == "Brave Fallback Result"
        assert results[0]["source"] == "brave"

def test_live_search_safe_empty_when_both_fail(mock_search_service):
    with patch("requests.get", side_effect=Exception("Network failure")):
        results = mock_search_service.live_search("Any query")
        assert results == []
