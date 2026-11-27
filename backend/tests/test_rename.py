# Tests for PATCH /api/conversations/{id} (rename a chat)
from sqlalchemy import text

URL = "/api/conversations"


def test_rename(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    response = alice.patch(f"{URL}/{chat_id}", json={"title": "Holiday questions"})
    assert response.status_code == 200
    assert response.json()["title"] == "Holiday questions"
    assert alice.get(f"{URL}/{chat_id}").json()["title"] == "Holiday questions"


def test_spaces_are_trimmed(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    assert alice.patch(f"{URL}/{chat_id}", json={"title": "  Expenses  "}).json()["title"] == "Expenses"


def test_bad_titles_are_refused(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={"title": "Original"}).json()["id"]
    for bad in [{"title": ""}, {"title": "   "}, {"title": "x" * 256}, {}]:
        assert alice.patch(f"{URL}/{chat_id}", json=bad).status_code == 422
    assert alice.get(f"{URL}/{chat_id}").json()["title"] == "Original"
    assert alice.patch(f"{URL}/{chat_id}", json={"title": "x" * 255}).status_code == 200  # the limit itself is fine


def test_rename_keeps_the_list_order(make_client, db):
    # renaming is not activity: the chat must not jump to the top of the sidebar
    alice = make_client("alice")
    older = alice.post(URL, json={"title": "older"}).json()["id"]
    alice.post(URL, json={"title": "newer"})
    # inside one test transaction now() is the same for every row, so move both chats into the past first
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 hour' WHERE title = 'newer'"))
    db.execute(text("UPDATE conversations SET updated_at = now() - interval '1 day' WHERE id = :id"), {"id": older})
    db.expire_all()
    before = alice.get(f"{URL}/{older}").json()["updated_at"]

    renamed = alice.patch(f"{URL}/{older}", json={"title": "older, renamed"}).json()
    assert renamed["updated_at"] == before
    assert [c["title"] for c in alice.get(URL).json()] == ["newer", "older, renamed"]


def test_list_shows_the_new_title(make_client):
    # the cached list is cleared, so the sidebar shows the new title at once
    alice = make_client("alice")
    chat_id = alice.post(URL, json={"title": "before"}).json()["id"]
    assert [c["title"] for c in alice.get(URL).json()] == ["before"]  # now cached
    alice.patch(f"{URL}/{chat_id}", json={"title": "after"})
    assert [c["title"] for c in alice.get(URL).json()] == ["after"]


def test_export_uses_the_new_title(make_client):
    alice = make_client("alice")
    chat_id = alice.post(URL, json={}).json()["id"]
    alice.patch(f"{URL}/{chat_id}", json={"title": "Vacation plans"})
    response = alice.get(f"{URL}/{chat_id}/export", params={"format": "md"})
    assert response.text.startswith("# Vacation plans")
    assert "vacation-plans" in response.headers["content-disposition"]


def test_cannot_rename_someone_elses_chat(make_client):
    bob = make_client("bob")
    chat_id = bob.post(URL, json={"title": "bob's chat"}).json()["id"]
    alice = make_client("alice")
    assert alice.patch(f"{URL}/{chat_id}", json={"title": "hacked"}).status_code == 404
    assert bob.get(f"{URL}/{chat_id}").json()["title"] == "bob's chat"


def test_unknown_chat_404(make_client):
    assert make_client("alice").patch(f"{URL}/999999999", json={"title": "x"}).status_code == 404


def test_login_required(client):
    assert client.patch(f"{URL}/1", json={"title": "x"}).status_code == 401
