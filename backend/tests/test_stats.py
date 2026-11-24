# Tests for GET /api/users/{user_id}/stats (a user's own usage numbers)


def my_id(client) -> int:
    return client.get("/api/auth/me").json()["id"]


def add_message(client, chat_id: int, role: str, tokens_used):
    client.post(f"/api/conversations/{chat_id}/messages", json={"role": role, "content": "x", "tokens_used": tokens_used})


def test_stats_new_user(make_client):
    alice = make_client("alice")
    response = alice.get(f"/api/users/{my_id(alice)}/stats")
    assert response.status_code == 200
    assert response.json() == {"total_conversations": 0, "total_tokens": 0, "avg_tokens_per_message": 0.0}


def test_stats_counts(make_client):
    alice = make_client("alice")
    first = alice.post("/api/conversations", json={}).json()["id"]
    second = alice.post("/api/conversations", json={}).json()["id"]
    add_message(alice, first, "user", 10)
    add_message(alice, first, "assistant", 30)
    add_message(alice, second, "user", None)  # no count: left out of the average
    add_message(alice, second, "assistant", 5)

    # another user's chat must not count
    bob = make_client("bob")
    add_message(bob, bob.post("/api/conversations", json={}).json()["id"], "user", 999)

    stats = alice.get(f"/api/users/{my_id(alice)}/stats").json()
    assert stats == {"total_conversations": 2, "total_tokens": 45, "avg_tokens_per_message": 15.0}


def test_stats_average_is_rounded(make_client):
    alice = make_client("alice")
    chat = alice.post("/api/conversations", json={}).json()["id"]
    for tokens in (1, 1, 2):  # 4 / 3 = 1.333...
        add_message(alice, chat, "user", tokens)
    assert alice.get(f"/api/users/{my_id(alice)}/stats").json()["avg_tokens_per_message"] == 1.3


def test_stats_other_user_403(make_client):
    bob = make_client("bob")
    bobs_id = my_id(bob)
    alice = make_client("alice")
    response = alice.get(f"/api/users/{bobs_id}/stats")
    assert response.status_code == 403


def test_stats_no_login_401(client):
    assert client.get("/api/users/1/stats").status_code == 401
