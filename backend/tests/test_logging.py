# Tests for the per-request log lines (RequestLogMiddleware in main.py) and the per-answer line (stream.py).
# pytest's `caplog` fixture captures every log line written during a test.
import logging
import re

import pytest

# the fake Ollama and helpers from the stream tests (importing a fixture makes it usable here)
from tests.test_stream import ask, broken_ollama, fake_ollama, new_chat, no_chunks, no_real_ollama, read_events  # noqa: F401


@pytest.fixture
def logs(caplog):
    # only the app's own "rag" lines, at INFO and above
    caplog.set_level(logging.INFO, logger="rag")
    return lambda: [r for r in caplog.records if r.name == "rag"]


def lines(records, start: str) -> list[str]:
    return [r.getMessage() for r in records if r.getMessage().startswith(start)]


def test_request_is_logged(client, logs):
    client.get("/api/health")
    [line] = lines(logs(), "request method=GET path=/api/health")
    assert re.fullmatch(r"request method=GET path=/api/health status=200 ms=\d+", line)


def test_error_status_is_logged(make_client, logs):
    alice = make_client("alice")
    alice.get("/api/conversations/999999999")
    assert lines(logs(), "request method=GET path=/api/conversations/999999999 status=404 ms=")


def test_no_login_is_logged_as_401(client, logs):
    client.get("/api/conversations")
    assert lines(logs(), "request method=GET path=/api/conversations status=401 ms=")


def test_query_string_is_not_logged(make_client, logs):
    alice = make_client("alice")
    alice.get("/api/conversations", params={"limit": 5, "offset": 0})
    [line] = lines(logs(), "request method=GET path=/api/conversations ")
    assert "limit" not in line and "?" not in line


def test_answer_is_logged_with_tokens(make_client, fake_ollama, no_chunks, logs):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    read_events(ask(alice, chat_id))

    [answer] = [r for r in logs() if r.getMessage().startswith("answer ")]
    assert answer.levelname == "INFO"
    assert re.fullmatch(
        rf"answer user=\d+ chat={chat_id} outcome=done first_token_ms=\d+ total_ms=\d+ "
        r"prompt_tokens=50 answer_tokens=2 chunks=0",
        answer.getMessage(),
    )
    # the whole stream request is logged too, after the answer has been sent
    assert lines(logs(), "request method=POST path=/api/stream status=200 ms=")


def test_failed_answer_is_logged_as_error(make_client, broken_ollama, logs):
    alice = make_client("alice")
    chat_id = new_chat(alice)
    read_events(ask(alice, chat_id))

    [answer] = [r for r in logs() if r.getMessage().startswith("answer ")]
    assert answer.levelname == "WARNING"
    assert re.fullmatch(
        rf"answer user=\d+ chat={chat_id} outcome=error error=RuntimeError first_token_ms=\d+",
        answer.getMessage(),
    )
    assert "Ollama crashed" not in answer.getMessage()  # only the error type, never its message
    assert not [m for m in lines(logs(), "answer ") if "outcome=done" in m]  # no "done" line for a failed answer


def test_no_question_or_answer_text_in_logs(make_client, fake_ollama, logs):
    # privacy: the logs hold numbers and paths only, never what people asked or what Llama answered
    alice = make_client("alice")
    read_events(ask(alice, new_chat(alice), question="My secret salary question"))
    everything = " ".join(r.getMessage() for r in logs())
    assert "secret salary" not in everything
    assert "27 holiday" not in everything  # part of the fake answer
