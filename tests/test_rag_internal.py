from starlette.testclient import TestClient
from app.server import app
from app.config import settings

client = TestClient(app)

def test_internal_ask_auth_enforcement():
    """Verify that POST /internal/ask strictly rejects requests lacking valid X-Internal-Secret."""
    # 1. No secret
    res_no_secret = client.post("/internal/ask", json={
        "email": "test@example.com",
        "question": "What is the latest AI news?"
    })
    assert res_no_secret.status_code == 401, f"Expected 401 without secret, got {res_no_secret.status_code}"

    # 2. Invalid secret
    res_wrong_secret = client.post(
        "/internal/ask",
        json={"email": "test@example.com", "question": "What is the latest AI news?"},
        headers={"X-Internal-Secret": "invalid_secret_key"}
    )
    assert res_wrong_secret.status_code == 401, f"Expected 401 with wrong secret, got {res_wrong_secret.status_code}"

def test_internal_ask_rag_answering():
    """Verify that POST /internal/ask returns a grounded answer and sources when authenticated."""
    headers = {
        "X-Internal-Secret": settings.INTERNAL_API_SECRET,
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": "test@example.com",
        "question": "What are the latest AI models and breakthroughs?"
    }
    res = client.post("/internal/ask", json=payload, headers=headers)
    print("\n[TEST RAG] Response status:", res.status_code)
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}: {res.text}"

    data = res.json()
    assert data.get("status") == "success"
    assert "answer" in data
    assert len(data["answer"]) > 20, "Expected non-trivial answer"
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0, "Expected at least 1 retrieved source"

    safe_answer = data['answer'].encode('ascii', 'replace').decode('ascii')
    print(f"[TEST RAG] Answer:\n{safe_answer}")
    print(f"[TEST RAG] Sources ({len(data['sources'])}):")
    for s in data["sources"]:
        safe_title = s.get('title', '').encode('ascii', 'replace').decode('ascii')
        print(f"   - [{s.get('source')}] {safe_title} ({s.get('date')})")
