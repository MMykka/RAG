# Tests for the chat list / stats cache (services/cache.py).
# pytest has no Redis, so these use the in-memory cache; the logic is the same as with Redis.
# The `reset_cache` fixture in conftest.py empties the cache before and after every test.
from sqlalchemy import text

import app.services.cache as cache
from app.models import Conversation, Message
# the fake Ollama and helpers from the stream tests (importing a fixture makes it usable here)
from tests.test_stream import ask, fake_ollama, new_chat, no_real_ollama, read_events  # noqa: F401

URL = "/api/conversations"


def my_id(client) -> int:
    return client.get("/api/auth/me").json()["id"]


def stats(client) -> dict:
    return client.get(f"/api/users/{my_id(client)}/stats").json()


def test_list_is_cached(make_client, db):
    # A chat written straight into the database (not through the API) does not clear the cache,
    # so the second read still shows the old, cached list. That proves the read came from the cache.
    alice = make_client("alice")
    assert alice.get(URL).json() == []

    db.add(Conversation(user_id=my_id(alice), title="sneaked in"))
    db.flush()
    assert alice.get(URL).json() == []  # served from the cache

    cache.clear_cache()
    assert [c["title"] for c in alice.get(URL).json()] == ["sneaked in"]  # fresh from the database


def test_each_page_is_cached_separately(make_client):
    # page 1 and page 2 are stored under different fields, so page 2 is not a copy of page 1
    alice = make_client("alice")
    for title in ["one", "two", "three"]:
        alice.post(URL, json={"title": title})
    page1 = [c["id"] for c in alice.get(URL, params={"limit": 2}).json()]
    page2 = [c["id"] for c in alice.get(URL, params={"limit": 2, "offset": 2}).json()]
    assert len(page1) == 2 and len(page2) == 1
    assert not set(page1) & set(page2)


def test_create_refreshes_list(make_client):
    alice = make_client("alice")
    assert alice.get(URL).json() == []  # cached as empty
    alice.post(URL, json={"title": "new one"})
    assert [c["title"] for c in alice.get(URL).json()] == ["new one"]


def test_delete_refreshes_list(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={"title": "to delete"}).json()["id"]
    assert len(alice.get(URL).json()) == 1  # cached with the chat
    assert alice.delete(f"{URL}/{chat_id}").status_code == 204
    assert alice.get(URL).json() == []


def test_cache_is_per_user(make_client):
    # alice's cached list is not shown to bob, and bob's changes do not touch alice's cache
    alice = make_client("alice")
    alice.post(URL, json={"title": "alice chat"})
    assert [c["title"] for c in alice.get(URL).json()] == ["alice chat"]

    bob = make_client("bob")
    assert bob.get(URL).json() == []
    bob.post(URL, json={"title": "bob chat"})
    assert [c["title"] for c in bob.get(URL).json()] == ["bob chat"]
    assert [c["title"] for c in alice.get(URL).json()] == ["alice chat"]


def test_stats_are_cached(make_client, db):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    assert stats(alice)["total_tokens"] == 0

    db.add(Message(conversation_id=chat_id, role="assistant", content="hi", tokens_used=99))
    db.flush()
    assert stats(alice)["total_tokens"] == 0  # served from the cache

    cache.clear_cache()
    assert stats(alice)["total_tokens"] == 99


def test_stream_refreshes_list_and_stats(make_client, fake_ollama, db):
    # an answer saves new token counts (fake Ollama: 50 prompt + 2 answer) and moves the chat to the top
    alice = make_client("alice")
    older = alice.post(URL, json={"title": "older"}).json()["id"]
    alice.post(URL, json={"title": "newer"})
    # inside one test transaction now() is the same for every row, so move both chats into the past first
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 hour' WHERE title = 'newer'"))
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 day' WHERE id = :id"), {"id": older})
    db.expire_all()
    cache.clear_cache()  # the SQL above bypassed the API, so start from a fresh read
    assert [c["title"] for c in alice.get(URL).json()] == ["newer", "older"]
    assert stats(alice)["total_tokens"] == 0

    read_events(ask(alice, older))
    assert stats(alice)["total_tokens"] == 52
    assert alice.get(URL).json()[0]["id"] == older


def test_cache_expires(make_client, db, monkeypatch):
    # the TTL is the safety net: once it has passed, the next read goes to the database again
    monkeypatch.setattr(cache, "CACHE_TTL_SECONDS", 0)
    alice = make_client("alice")
    assert alice.get(URL).json() == []

    db.add(Conversation(user_id=my_id(alice), title="sneaked in"))
    db.flush()
    assert [c["title"] for c in alice.get(URL).json()] == ["sneaked in"]  # the cached copy had already expired
