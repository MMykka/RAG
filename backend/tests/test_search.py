# Tests for GET /api/conversations/search (Postgres full-text search over your own chats)
URL = "/api/conversations"
START, STOP = "\x02", "\x03"  # around each matching word in a snippet


def chat_with(client, title: str, *messages: str) -> int:
    chat_id = client.post(URL, json={"title": title}).json()["id"]
    for i, content in enumerate(messages):
        client.post(f"{URL}/{chat_id}/messages", json={"role": "user" if i % 2 == 0 else "assistant", "content": content})
    return chat_id


def search(client, q: str, **params):
    return client.get(f"{URL}/search", params={"q": q, **params})


def test_finds_a_word_in_a_message(make_client):
    alice = make_client("alice")
    hit_id = chat_with(alice, "New chat", "How many holiday days do I get?", "You get 27 paid holiday days.")
    chat_with(alice, "Other", "Where is the printer?")
    results = search(alice, "holiday").json()
    assert [r["id"] for r in results] == [hit_id]
    assert f"{START}holiday{STOP}" in results[0]["snippet"]
    assert results[0]["message_id"] is not None


def test_word_forms_match(make_client):
    # stemming: "holidays" finds "holiday" and the other way round
    alice = make_client("alice")
    chat_id = chat_with(alice, "New chat", "My holiday plans")
    assert [r["id"] for r in search(alice, "holidays").json()] == [chat_id]


def test_title_match_without_message_match(make_client):
    alice = make_client("alice")
    chat_id = chat_with(alice, "Expense report", "nothing related here")
    [hit] = search(alice, "expense").json()
    assert hit["id"] == chat_id and hit["snippet"] is None and hit["message_id"] is None


def test_title_match_ranks_first(make_client):
    alice = make_client("alice")
    in_message = chat_with(alice, "Random", "a question about parking")
    in_title = chat_with(alice, "Parking", "something else")
    assert [r["id"] for r in search(alice, "parking").json()] == [in_title, in_message]


def test_phrase_and_exclusion(make_client):
    # Google-style input: "exact phrase" and -word
    alice = make_client("alice")
    sick_leave = chat_with(alice, "A", "How does sick leave work?")
    leave_policy = chat_with(alice, "B", "Leave the office sick? Call your manager.")
    assert [r["id"] for r in search(alice, '"sick leave"').json()] == [sick_leave]
    assert [r["id"] for r in search(alice, "leave -office").json()] == [sick_leave]
    assert {r["id"] for r in search(alice, "sick leave").json()} == {sick_leave, leave_policy}


def test_one_result_per_chat(make_client):
    alice = make_client("alice")
    chat_id = chat_with(alice, "New chat", "laptop question", "laptop answer", "more about the laptop")
    assert [r["id"] for r in search(alice, "laptop").json()] == [chat_id]


def test_no_match(make_client):
    alice = make_client("alice")
    chat_with(alice, "New chat", "hello")
    assert search(alice, "spaceship").json() == []


def test_only_your_own_chats(make_client):
    bob = make_client("bob")
    chat_with(bob, "Bob's salary", "my salary is secret")
    alice = make_client("alice")
    own = chat_with(alice, "Mine", "salary question")
    results = search(alice, "salary").json()
    assert [r["id"] for r in results] == [own]
    assert "secret" not in str(results)


def test_new_messages_are_searchable_at_once(make_client):
    # the search column is filled by Postgres on insert, nothing to rebuild
    alice = make_client("alice")
    chat_id = chat_with(alice, "New chat")
    assert search(alice, "invoice").json() == []
    alice.post(f"{URL}/{chat_id}/messages", json={"role": "user", "content": "Where do I send an invoice?"})
    assert [r["id"] for r in search(alice, "invoice").json()] == [chat_id]


def test_odd_input_is_safe(make_client):
    # punctuation, quotes and SQL-looking text never cause an error (the query is a bound parameter)
    alice = make_client("alice")
    chat_with(alice, "New chat", "hello world")
    for q in ['hello"', "it's", "'; DROP TABLE messages; --", "a & b | !c", "((("]:
        assert search(alice, q).status_code == 200


def test_validation(make_client):
    alice = make_client("alice")
    assert search(alice, "a").status_code == 422          # too short
    assert search(alice, "x" * 201).status_code == 422    # too long
    assert alice.get(f"{URL}/search").status_code == 422  # missing
    assert search(alice, "hello", limit=0).status_code == 422


def test_limit(make_client):
    alice = make_client("alice")
    for i in range(5):
        chat_with(alice, f"Chat {i}", "budget numbers")
    assert len(search(alice, "budget", limit=3).json()) == 3


def test_login_required(client):
    assert search(client, "hello").status_code == 401


def test_chat_ids_still_work(make_client):
    # "/search" must not break "/{conversation_id}"
    alice = make_client("alice")
    chat_id = chat_with(alice, "New chat")
    assert alice.get(f"{URL}/{chat_id}").status_code == 200
