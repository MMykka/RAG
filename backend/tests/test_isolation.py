# Pre-launch check: user A can never read, change, export, delete or see stats of user B's data.
# Every endpoint that takes a chat id or user id is tried by "alice" against "bob"'s data.
# 404 (not 403) for chats: alice cannot even tell whether chat 12 exists.
import pytest

# the fake Ollama and helpers from the stream tests (importing a fixture makes it usable here)
from tests.test_stream import ask, fake_ollama, no_real_ollama, read_events  # noqa: F401

URL = "/api/conversations"


@pytest.fixture
def alice_and_bob(make_client):
    # bob has one chat with two messages; alice is logged in and owns nothing yet
    bob = make_client("bob")
    chat = bob.post(URL, json={"title": "bob's private chat"}).json()
    bob.post(f"{URL}/{chat['id']}/messages", json={"role": "user", "content": "bob's question"})
    bob.post(f"{URL}/{chat['id']}/messages", json={"role": "assistant", "content": "bob's answer", "tokens_used": 7})
    alice = make_client("alice")
    return alice, bob, chat["id"]


def bob_chat_is_untouched(bob, chat_id):
    chat = bob.get(f"{URL}/{chat_id}")
    assert chat.status_code == 200
    body = chat.json()
    assert body["title"] == "bob's private chat"
    assert [m["content"] for m in body["messages"]] == ["bob's question", "bob's answer"]


def my_id(client) -> int:
    return client.get("/api/auth/me").json()["id"]


def test_cannot_list(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    assert alice.get(URL).json() == []
    assert chat_id not in [c["id"] for c in alice.get(URL, params={"limit": 100}).json()]


def test_cannot_read(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    response = alice.get(f"{URL}/{chat_id}")
    assert response.status_code == 404
    assert "bob" not in response.text


def test_cannot_add_messages(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    response = alice.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "alice sneaks in"})
    assert response.status_code == 404
    bob_chat_is_untouched(bob, chat_id)


def test_cannot_delete(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    assert alice.delete(f"{URL}/{chat_id}").status_code == 404
    bob_chat_is_untouched(bob, chat_id)


@pytest.mark.parametrize("fmt", ["md", "json"])
def test_cannot_export(alice_and_bob, fmt):
    alice, bob, chat_id = alice_and_bob
    response = alice.get(f"{URL}/{chat_id}/export", params={"format": fmt})
    assert response.status_code == 404
    assert "bob" not in response.text
    assert "attachment" not in response.headers.get("content-disposition", "")


def test_cannot_stream_into(alice_and_bob, fake_ollama):
    alice, bob, chat_id = alice_and_bob
    response = ask(alice, chat_id, question="alice asks in bob's chat")
    assert response.status_code == 404
    assert fake_ollama == []  # Llama was never asked
    bob_chat_is_untouched(bob, chat_id)


def test_cannot_see_stats(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    response = alice.get(f"/api/users/{my_id(bob)}/stats")
    assert response.status_code == 403
    assert "total_tokens" not in response.text


def test_own_stats_do_not_include_others(alice_and_bob):
    alice, bob, chat_id = alice_and_bob
    assert alice.get(f"/api/users/{my_id(alice)}/stats").json() == {
        "total_conversations": 0, "total_tokens": 0, "avg_tokens_per_message": 0.0,
    }
    assert bob.get(f"/api/users/{my_id(bob)}/stats").json()["total_tokens"] == 7


def test_user_id_in_body_or_query_is_ignored(alice_and_bob):
    # a chat alice creates is always hers, whatever user id she sends
    alice, bob, chat_id = alice_and_bob
    bob_id = my_id(bob)
    made = alice.post(URL, json={"title": "mine", "user_id": bob_id}).json()
    assert made["user_id"] == my_id(alice)
    assert alice.get(URL, params={"user_id": bob_id}).json()[0]["id"] == made["id"]
    assert [c["id"] for c in bob.get(URL).json()] == [chat_id]


def test_cache_does_not_leak_between_users(alice_and_bob):
    # bob's list is cached first; alice must still get her own (empty) list, not bob's cached one
    alice, bob, chat_id = alice_and_bob
    assert [c["id"] for c in bob.get(URL).json()] == [chat_id]
    assert alice.get(URL).json() == []
    assert alice.get(f"/api/users/{my_id(alice)}/stats").json()["total_tokens"] == 0


def test_forged_cookie_is_rejected(alice_and_bob, client):
    # a made-up or tampered login cookie gives 401, never someone's data
    alice, bob, chat_id = alice_and_bob
    token = alice.cookies.get("access_token")
    client.cookies.set("access_token", token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB"))
    assert client.get(URL).status_code == 401
    assert client.get(f"{URL}/{chat_id}").status_code == 401
