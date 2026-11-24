# Reads the company documents in the root documents/ folder, cuts them into pieces,
# turns each piece into 768 numbers with nomic-embed-text and saves them in the chunks table.
# Run from backend/:  .venv\Scripts\python.exe -m scripts.ingest_documents
# Running it again replaces each file's old pieces, so it never stores duplicates.
#
# How documents are cut (see RAG_FIXES.md, fix 1):
#   - Markdown is cut at its "#" and "##" headings, so every section (one policy,
#     one chapter) is its own piece and keeps its title.
#   - A section longer than CHUNK_SIZE is cut again into overlapping parts, and its
#     heading is repeated at the top of every part, so no part loses its title.
#   - Text without headings (most .txt files) is cut every CHUNK_SIZE characters.
import re
from pathlib import Path

from app.database import SessionLocal
from app.repositories.chunks import replace_chunks
from app.services.llm import embed_documents

# backend/scripts/ingest_documents.py -> parents[2] is the project root
DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"
FILE_TYPES = {".txt", ".md"}
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# A Markdown heading of level 1 or 2 ("# Title", "## POL-13: ..."). Deeper headings
# ("### ...") stay inside their section, so they keep their parent's title.
SECTION_HEADING = re.compile(r"^#{1,2} \S")
CODE_FENCE = re.compile(r"^(```|~~~)")


def split_sections(text: str) -> list[str]:
    # Cut the text into sections, each starting at a heading. Text before the first
    # heading is a section of its own. "#" lines inside ``` code blocks are not headings.
    sections, current, in_code = [], [], False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_code = not in_code
        if not in_code and SECTION_HEADING.match(line) and current:
            sections.append("\n".join(current))
            current = []
        current.append(line)
    sections.append("\n".join(current))
    # Drop sections that hold nothing but separators ("---") or blank lines
    return [s.strip() for s in sections if s.strip().strip("-").strip()]


def split_document(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    # The pieces of one document: one per section, long sections cut into parts
    # that each start with the section's heading.
    pieces = []
    for section in split_sections(text):
        if len(section) <= size:
            pieces.append(section)
            continue
        first_line, _, rest = section.partition("\n")
        if SECTION_HEADING.match(first_line):
            heading, body = first_line, rest.strip()
            room = size - len(heading) - 2  # the heading and a blank line come first
            pieces += [f"{heading}\n\n{part}" for part in split_text(body, room, min(overlap, room // 2))]
        else:
            pieces += split_text(section, size, overlap)
    return pieces


def split_text(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    # Cut the text into pieces of `size` characters. Each piece starts `size - overlap`
    # characters after the previous one, so it repeats the last 200 characters of the one
    # before it and a sentence cut at a boundary still appears whole in one piece.
    pieces = []
    start = 0
    while start < len(text):
        pieces.append(text[start:start + size])
        # This piece reached the end of the text, so stop. Otherwise the next piece
        # would only repeat the end of this one.
        if start + size >= len(text):
            break
        start += size - overlap
    return pieces


def main() -> None:
    files = sorted(f for f in DOCUMENTS_DIR.iterdir() if f.suffix.lower() in FILE_TYPES)
    if not files:
        print(f"No .txt or .md files in {DOCUMENTS_DIR}")
        return

    with SessionLocal() as db:
        for file in files:
            # utf-8-sig also removes the invisible BOM mark Windows editors put at the start of a file.
            text = file.read_text(encoding="utf-8-sig").strip()
            if not text:
                print(f"{file.name}: empty, skipped")
                continue

            pieces = split_document(text)
            embeddings = embed_documents(pieces)
            replace_chunks(db, file.name, pieces, embeddings)
            print(f"{file.name}: {len(pieces)} chunks")


if __name__ == "__main__":
    main()
