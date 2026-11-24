# Tests for how scripts/ingest_documents.py cuts documents into pieces (no database, no Ollama)
from scripts.ingest_documents import split_document, split_text

HANDBOOK = """# Handbook

Intro line.

---

## POL-01: Hours

- Work 9 to 5.

---

## POL-02: Equipment

- Laptops stay company property.
"""


def test_markdown_is_cut_at_headings():
    pieces = split_document(HANDBOOK)
    assert pieces == [
        "# Handbook\n\nIntro line.\n\n---",
        "## POL-01: Hours\n\n- Work 9 to 5.\n\n---",
        "## POL-02: Equipment\n\n- Laptops stay company property.",
    ]


def test_every_piece_keeps_its_heading():
    # the problem this fixes: a policy's rules ending up in a piece without its title
    for piece in split_document(HANDBOOK):
        assert piece.startswith("#")


def test_long_section_repeats_its_heading_in_every_part():
    body = " ".join(f"rule{i}" for i in range(400))  # ~3000 characters
    pieces = split_document(f"## POL-09: Security\n\n{body}", size=1000, overlap=200)
    assert len(pieces) > 1
    assert all(p.startswith("## POL-09: Security\n\n") for p in pieces)
    assert all(len(p) <= 1000 for p in pieces)
    # nothing is lost: the parts, minus the repeated heading and the overlap, rebuild the body
    parts = [p[len("## POL-09: Security\n\n"):] for p in pieces]
    overlap = min(200, (1000 - len("## POL-09: Security") - 2) // 2)
    assert parts[0] + "".join(part[overlap:] for part in parts[1:]) == body


def test_deeper_headings_stay_in_their_section():
    text = "## POL-05: Leave\n\nIntro.\n\n### Birth parents\n\n16 weeks."
    assert split_document(text) == [text]


def test_hash_lines_in_code_blocks_are_not_headings():
    text = "## Setup\n\n```bash\n# install\npip install x\n```\n\nDone."
    assert split_document(text) == [text]


def test_text_without_headings_is_cut_by_size():
    text = "x" * 2500
    assert split_document(text, size=1000, overlap=200) == split_text(text, 1000, 200)
    assert [len(p) for p in split_document(text)] == [1000, 1000, 900]


def test_separator_only_sections_are_dropped():
    assert split_document("---\n\n## A\n\nText") == ["## A\n\nText"]
