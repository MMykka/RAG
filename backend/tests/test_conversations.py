from sqlalchemy import text

URL = "/api/conversations"


# ---------- create ----------

def test_create_with_title(make_client):
    alice = make_client("alice")
    r = alice.post(URL, json={"title": "My chat"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "My chat"
    assert body["user_id"] == alice.get("/api/auth/me").json()["id"]


def test_create_without_title_gets_default(make_client):
    alice = make_client("alice")
    r = alice.post(URL, json={})
    assert r.status_code == 201
    assert r.json()["title"] == "New chat"


def test_create_ignores_user_id_in_body(make_client):
    # the owner always comes from the login cookie, never from the request
    alice = make_client("alice")
    bob = make_client("bob")
    bob_id = bob.get("/api/auth/me").json()["id"]
    r = alice.post(URL, json={"title": "sneaky", "user_id": bob_id})
    assert r.status_code == 201
    assert r.json()["user_id"] != bob_id


# ---------- list ----------

def test_list_shows_only_own_chats(make_client):
    alice = make_client("alice")
    bob = make_client("bob")
    alice.post(URL, json={"title": "alice 1"})
    alice.post(URL, json={"title": "alice 2"})
    bob.post(URL, json={"title": "bob 1"})

    assert sorted(c["title"] for c in alice.get(URL).json()) == ["alice 1", "alice 2"]
    assert [c["title"] for c in bob.get(URL).json()] == ["bob 1"]


def test_list_pagination(make_client):
    alice = make_client("alice")
    for i in range(3):
        alice.post(URL, json={"title": f"chat {i}"})

    page1 = alice.get(URL, params={"limit": 2, "offset": 0}).json()
    page2 = alice.get(URL, params={"limit": 2, "offset": 2}).json()
    assert len(page1) == 2
    assert len(page2) == 1
    assert {c["id"] for c in page1}.isdisjoint({c["id"] for c in page2})


def test_list_rejects_bad_limit(make_client):
    alice = make_client("alice")
    assert alice.get(URL, params={"limit": 0}).status_code == 422
    assert alice.get(URL, params={"limit": 101}).status_code == 422
    assert alice.get(URL, params={"offset": -1}).status_code == 422


# ---------- get one + messages ----------

def test_get_one_with_messages_in_order(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={"title": "x"}).json()["id"]
    alice.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "hello"})
    alice.post(f"{URL}/{chat_id}/messages", json={"role": "assistant", "content": "hi there", "tokens_used": 7})

    r = alice.get(f"{URL}/{chat_id}")
    assert r.status_code == 200
    messages = r.json()["messages"]
    assert [m["content"] for m in messages] == ["hello", "hi there"]
    assert messages[0]["tokens_used"] is None
    assert messages[1]["tokens_used"] == 7


def test_get_one_without_messages(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    assert alice.get(f"{URL}/{chat_id}").json()["messages"] == []


def test_get_unknown_chat_404(make_client):
    alice = make_client("alice")
    r = alice.get(f"{URL}/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Conversation not found"


# ---------- save message ----------

def test_save_message(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    r = alice.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "hello"})
    assert r.status_code == 201
    assert r.json()["role"] == "user"
    assert r.json()["content"] == "hello"


def test_message_moves_chat_to_top(make_client, db):
    alice = make_client("alice")
    older = alice.post(URL, json={"title": "older"}).json()["id"]
    alice.post(URL, json={"title": "newer"})

    # inside one test transaction now() is the same for every row, so move both chats into the past first:
    # "older" a day back, "newer" an hour back; the message bump then sets "older" to now(), the newest time
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 hour' WHERE title = 'newer'"))
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 day' WHERE id = :id"), {"id": older})
    db.expire_all()
    assert [c["title"] for c in alice.get(URL).json()] == ["newer", "older"]

    # a new message bumps updated_at, so "older" moves to the top
    alice.post(f"{URL}/{older}/messages", json={"role": "user", "content": "bump"})
    assert [c["title"] for c in alice.get(URL).json()][0] == "older"


# ---------- delete ----------

def test_delete_removes_chat(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    alice.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "bye"})

    r = alice.delete(f"{URL}/{chat_id}")
    assert r.status_code == 204
    assert alice.get(f"{URL}/{chat_id}").status_code == 404
    assert alice.get(URL).json() == []


def test_delete_twice_404(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    alice.delete(f"{URL}/{chat_id}")
    assert alice.delete(f"{URL}/{chat_id}").status_code == 404


# ---------- ownership ----------

def test_other_user_cannot_touch_my_chat(make_client):
    alice = make_client("alice")
    bob = make_client("bob")
    chat_id = alice.post(URL, json={"title": "private"}).json()["id"]

    assert bob.get(f"{URL}/{chat_id}").status_code == 404
    assert bob.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "x"}).status_code == 404
    assert bob.delete(f"{URL}/{chat_id}").status_code == 404

    # still there, untouched
    r = alice.get(f"{URL}/{chat_id}")
    assert r.status_code == 200
    assert r.json()["messages"] == []


# ---------- not logged in ----------

def test_all_endpoints_need_login(client):
    assert client.post(URL, json={"title": "x"}).status_code == 401
    assert client.get(URL).status_code == 401
    assert client.get(f"{URL}/1").status_code == 401
    assert client.post(f"{URL}/1/messages", json={"role": "user", "content": "x"}).status_code == 401
    assert client.delete(f"{URL}/1").status_code == 401


# ---------- validation ----------

def test_title_validation(make_client):
    alice = make_client("alice")
    assert alice.post(URL, json={"title": ""}).status_code == 422
    assert alice.post(URL, json={"title": "x" * 256}).status_code == 422
    assert alice.post(URL, json={"title": "x" * 255}).status_code == 201


def test_message_validation(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    url = f"{URL}/{chat_id}/messages"
    assert alice.post(url, json={"role": "admin", "content": "x"}).status_code == 422
    assert alice.post(url, json={"role": "user", "content": ""}).status_code == 422
    assert alice.post(url, json={"role": "user"}).status_code == 422
    assert alice.post(url, json={"role": "user", "content": "x", "tokens_used": -1}).status_code == 422
