# Tests for GET /api/conversations/{id}/export (Markdown and JSON downloads)
import json

from app.config import settings


def chat_with_messages(client, title="Holiday questions"):
    # a chat with a question and an answer (with token counts and a source)
    chat_id = client.post("/api/conversations", json={"title": title}).json()["id"]
    client.post(f"/api/conversations/{chat_id}/messages", json={"role": "user", "content": "How many vacation days?", "tokens_used": 40})
    client.post(
        f"/api/conversations/{chat_id}/messages",
        json={"role": "assistant", "content": "You get 22 days.", "tokens_used": 6, "sources": [{"source": "policies.md", "chunk_index": 3}]},
    )
    return chat_id


def test_export_markdown(make_client):
    alice = make_client("alice")
    chat_id = chat_with_messages(alice)
    response = alice.get(f"/api/conversations/{chat_id}/export?format=md")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == f'attachment; filename="chat-{chat_id}-holiday-questions.md"'
    text = response.text
    assert text.startswith("# Holiday questions\n")  # title as h1
    # user and assistant in order, each with its label
    assert text.index("**You**") < text.index("How many vacation days?") < text.index("**Assistant**") < text.index("You get 22 days.")
    assert "2 messages" in text


def test_export_markdown_is_the_default(make_client):
    alice = make_client("alice")
    chat_id = chat_with_messages(alice)
    response = alice.get(f"/api/conversations/{chat_id}/export")
    assert response.status_code == 200
    assert response.text.startswith("# Holiday questions")


def test_export_json(make_client):
    alice = make_client("alice")
    chat_id = chat_with_messages(alice)
    response = alice.get(f"/api/conversations/{chat_id}/export?format=json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == f'attachment; filename="chat-{chat_id}-holiday-questions.json"'
    data = json.loads(response.text)
    assert data["conversation"]["id"] == chat_id
    assert data["conversation"]["title"] == "Holiday questions"
    assert data["model"] == settings.ollama_model
    assert data["message_count"] == 2
    assert data["total_tokens"] == 46
    assert "exported_at" in data
    first, second = data["messages"]
    assert (first["role"], first["content"], first["tokens_used"], first["sources"]) == ("user", "How many vacation days?", 40, None)
    assert (second["role"], second["tokens_used"], second["sources"]) == ("assistant", 6, [{"source": "policies.md", "chunk_index": 3}])
    assert "created_at" in first


def test_export_empty_chat(make_client):
    alice = make_client("alice")
    chat_id = alice.post("/api/conversations", json={}).json()["id"]
    md = alice.get(f"/api/conversations/{chat_id}/export?format=md")
    assert md.text.startswith("# New chat") and "0 messages" in md.text
    data = alice.get(f"/api/conversations/{chat_id}/export?format=json").json()
    assert data["messages"] == [] and data["total_tokens"] == 0


def test_export_filename_is_safe(make_client):
    alice = make_client("alice")
    chat_id = alice.post("/api/conversations", json={"title": 'Q3 "budget" / plans: ünïcode?'}).json()["id"]
    header = alice.get(f"/api/conversations/{chat_id}/export").headers["content-disposition"]
    assert header == f'attachment; filename="chat-{chat_id}-q3-budget-plans-n-code.md"'


def test_export_other_users_chat_404(make_client):
    bob = make_client("bob")
    bobs_chat = chat_with_messages(bob)
    alice = make_client("alice")
    assert alice.get(f"/api/conversations/{bobs_chat}/export?format=md").status_code == 404
    assert alice.get(f"/api/conversations/{bobs_chat}/export?format=json").status_code == 404


def test_export_unknown_format_422(make_client):
    alice = make_client("alice")
    chat_id = chat_with_messages(alice)
    assert alice.get(f"/api/conversations/{chat_id}/export?format=pdf").status_code == 422


def test_export_no_login_401(client):
    assert client.get("/api/conversations/1/export").status_code == 401
