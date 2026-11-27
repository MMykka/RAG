# Tests for GET /api/documents (the knowledge base list).
from app.models.chunks import Chunk
from tests.test_stream import no_chunks, vector  # noqa: F401  (no_chunks empties the table inside the rolled-back test)

URL = "/api/documents"


def add_chunks(db, source: str, texts: list[str]):
    db.add_all([Chunk(source=source, chunk_index=i, content=t, embedding=vector(i)) for i, t in enumerate(texts)])
    db.flush()


def test_empty_knowledge_base(make_client, no_chunks):
    assert make_client("alice").get(URL).json() == []


def test_one_row_per_document(make_client, db, no_chunks):
    add_chunks(db, "policies.md", ["## POL-1\nholidays", "## POL-2\nsick leave", "## POL-3\nequipment"])
    add_chunks(db, "faq.txt", ["Where is the coffee?"])

    docs = make_client("alice").get(URL).json()
    assert [d["name"] for d in docs] == ["faq.txt", "policies.md"]  # sorted by name
    faq, policies = docs
    assert policies["chunks"] == 3 and faq["chunks"] == 1
    assert faq["size_bytes"] == len("Where is the coffee?".encode())
    assert policies["size_bytes"] == sum(len(t.encode()) for t in ["## POL-1\nholidays", "## POL-2\nsick leave", "## POL-3\nequipment"])
    assert policies["added"]  # a timestamp


def test_size_counts_bytes_not_letters(make_client, db, no_chunks):
    add_chunks(db, "café.md", ["café"])  # é is 2 bytes in UTF-8
    [doc] = make_client("alice").get(URL).json()
    assert doc["size_bytes"] == 5


def test_every_user_sees_the_same_list(make_client, db, no_chunks):
    # the knowledge base is shared: it does not belong to one user
    add_chunks(db, "policies.md", ["text"])
    assert make_client("alice").get(URL).json() == make_client("bob").get(URL).json()


def test_no_content_or_embeddings_in_the_list(make_client, db, no_chunks):
    add_chunks(db, "policies.md", ["secret policy text"])
    body = make_client("alice").get(URL).text
    assert "secret policy text" not in body
    assert "embedding" not in body


def test_login_required(client):
    assert client.get(URL).status_code == 401
