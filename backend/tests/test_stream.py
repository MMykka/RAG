# Tests for POST /api/stream. Ollama is never called: the fixtures below swap it for fakes,
# so these tests are instant, give the same answer every time and pass on a PC without Ollama.
import json

import pytest
from ollama import Client

import app.routers.stream as stream_router
import app.services.llm as llm
import app.services.rag as rag
from app.models.chunks import Chunk
from app.config import settings
from app.services.cache import active_generations

ANSWER_PIECES = ["You get ", "27 holiday ", "days."]
ANSWER = "".join(ANSWER_PIECES)


def vector(position: int) -> list[float]:
    # a 768-number vector pointing in one direction; same position = same meaning, other position = unrelated
    numbers = [0.0] * 768
    numbers[position] = 1.0
    return numbers


def read_events(response) -> list[dict]:
    # the body is "data: {...}" blocks separated by a blank line; turn each block into a dict
    blocks = [block for block in response.text.split("\n\n") if block]
    assert all(block.startswith("data: ") for block in blocks)
    return [json.loads(block[len("data: "):]) for block in blocks]


@pytest.fixture(autouse=True)
def no_real_ollama(monkeypatch):
    # safety net: if a test reaches the real Ollama by mistake, it fails instead of using the model
    monkeypatch.setattr(llm, "client", Client(host="http://127.0.0.1:9"))


@pytest.fixture
def fake_ollama(monkeypatch):
    # replaces the answer (stream_chat) and the question's vector (embed_query) with fixed fakes.
    # stream.py and rag.py each hold their own copy of these names, so those copies are the ones replaced.
    calls = []  # every message list the fake "Llama" received, so tests can check the prompt

    def fake_stream_chat(messages, usage):
        calls.append(messages)
        yield from ANSWER_PIECES
        usage["prompt"] = 50
        usage["answer"] = 2

    monkeypatch.setattr(stream_router, "stream_chat", fake_stream_chat)
    monkeypatch.setattr(rag, "embed_query", lambda text: vector(0))
    return calls


@pytest.fixture
def broken_ollama(monkeypatch):
    # an Ollama that sends one piece and then dies
    def failing_stream_chat(messages, usage):
        yield "You get "
        raise RuntimeError("Ollama crashed")

    monkeypatch.setattr(stream_router, "stream_chat", failing_stream_chat)
    monkeypatch.setattr(rag, "embed_query", lambda text: vector(0))


@pytest.fixture
def no_chunks(db):
    # Start from an empty knowledge base, so the test does not depend on the real documents.
    # This runs inside the test's transaction, which is rolled back: the real chunks stay.
    db.query(Chunk).delete()
    db.flush()


def new_chat(client) -> int:
    return client.post("/api/conversations", json={}).json()["id"]


def ask(client, chat_id: int, question: str = "How many holiday days do I get?"):
    return client.post("/api/stream", json={"conversation_id": chat_id, "content": question})


def test_stream_events(make_client, fake_ollama):
    alice = make_client("alice")
    response = ask(alice, new_chat(alice))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = read_events(response)
    tokens, done = events[:-1], events[-1]
    assert [e["token"] for e in tokens] == ANSWER_PIECES
    assert [e["text"] for e in tokens] == ["You get ", "You get 27 holiday ", ANSWER]  # text grows piece by piece
    assert all(0 <= e["percent"] <= 99 for e in tokens)
    assert done["done"] is True
    assert done["text"] == ANSWER
    assert done["percent"] == 100


def test_stream_saves_messages(make_client, fake_ollama):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    ask(alice, chat_id)

    messages = alice.get(f"/api/conversations/{chat_id}").json()["messages"]
    assert [(m["role"], m["content"]) for m in messages] == [("user", "How many holiday days do I get?"), ("assistant", ANSWER)]
    assert messages[0]["tokens_used"] == 50  # prompt tokens on the user message
    assert messages[1]["tokens_used"] == 2   # answer tokens on the assistant message


def test_stream_uses_chunks(make_client, fake_ollama, db, no_chunks):
    db.add_all([
        Chunk(source="holiday.md", chunk_index=3, content="Every employee gets 27 holiday days.", embedding=vector(0)),
        Chunk(source="office.md", chunk_index=0, content="The office opens at 8:30.", embedding=vector(1)),
    ])
    db.flush()
    alice = make_client("alice")
    chat_id = new_chat(alice)
    done = read_events(ask(alice, chat_id))[-1]

    # the prompt Llama got: a system message with the documents, then the question on its own
    prompt = fake_ollama[0]
    assert [m["role"] for m in prompt] == ["system", "user"]
    assert "Every employee gets 27 holiday days." in prompt[0]["content"]
    assert prompt[1]["content"] == "How many holiday days do I get?"

    # the closest chunk (same direction as the question) comes first
    expected = [{"source": "holiday.md", "chunk_index": 3}, {"source": "office.md", "chunk_index": 0}]
    assert done["sources"] == expected
    saved = alice.get(f"/api/conversations/{chat_id}").json()["messages"]
    assert saved[1]["sources"] == expected
    assert saved[0]["sources"] is None  # the user's message has no sources


def test_stream_without_chunks(make_client, fake_ollama, no_chunks):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    done = read_events(ask(alice, chat_id))[-1]

    assert fake_ollama[0] == [{"role": "user", "content": "How many holiday days do I get?"}]
    assert done["sources"] == []
    saved = alice.get(f"/api/conversations/{chat_id}").json()["messages"]
    assert saved[1]["sources"] is None


def test_stream_error(make_client, broken_ollama):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    events = read_events(ask(alice, chat_id))

    assert events[-1] == {"error": "The AI stopped answering. Please try again.", "text": "You get "}
    assert not any(e.get("done") for e in events)
    saved = alice.get(f"/api/conversations/{chat_id}").json()["messages"]
    assert [m["role"] for m in saved] == ["user"]  # the half answer is not saved


def test_stream_other_user_404(make_client, fake_ollama):
    bob = make_client("bob")
    bobs_chat = new_chat(bob)
    alice = make_client("alice")

    assert ask(alice, bobs_chat).status_code == 404
    assert bob.get(f"/api/conversations/{bobs_chat}").json()["messages"] == []
    assert fake_ollama == []  # Llama was never asked


def test_stream_empty_content_422(make_client, fake_ollama):
    alice = make_client("alice")
    assert ask(alice, new_chat(alice), question="").status_code == 422
    assert fake_ollama == []


def test_stream_no_login_401(client, fake_ollama):
    assert ask(client, 1).status_code == 401
    assert fake_ollama == []


def test_stream_rate_limit_per_user(make_client, fake_ollama):
    # 20 questions per minute per user: the 21st gets 429, and another user is not affected
    alice = make_client("alice")
    chat_id = new_chat(alice)
    for _ in range(20):
        assert ask(alice, chat_id).status_code == 200

    blocked = ask(alice, chat_id)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Too many questions. Please wait a minute and try again."}
    assert len(fake_ollama) == 20  # Llama was not asked the 21st time

    bob = make_client("bob")
    assert ask(bob, new_chat(bob)).status_code == 200  # bob has a separate counter


def test_stream_busy_503(make_client, fake_ollama, monkeypatch):
    # every generation slot taken (cap 0): refused before anything is saved or Llama is asked
    monkeypatch.setattr(settings, "max_generations", 0)
    alice = make_client("alice")
    chat_id = new_chat(alice)

    response = ask(alice, chat_id)
    assert response.status_code == 503
    assert response.json() == {"detail": "The server is busy. Please try again."}
    assert fake_ollama == []
    assert alice.get(f"/api/conversations/{chat_id}").json()["messages"] == []


def test_stream_releases_slot(make_client, fake_ollama):
    # after an answer the slot is given back
    alice = make_client("alice")
    chat_id = new_chat(alice)
    assert active_generations() == 0
    ask(alice, chat_id)
    assert active_generations() == 0


def test_stream_releases_slot_on_error(make_client, broken_ollama):
    alice = make_client("alice")
    read_events(ask(alice, new_chat(alice)))
    assert active_generations() == 0
