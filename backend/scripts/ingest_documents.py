# Reads the company documents in the root documents/ folder, cuts them into pieces,
# turns each piece into 768 numbers with nomic-embed-text and saves them in the chunks table.
# Run from backend/:  .venv\Scripts\python.exe -m scripts.ingest_documents
# Running it again replaces each file's old pieces, so it never stores duplicates.
from pathlib import Path

from app.database import SessionLocal
from app.repositories.chunks import replace_chunks
from app.services.llm import embed_documents

# backend/scripts/ingest_documents.py -> parents[2] is the project root
DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"
FILE_TYPES = {".txt", ".md"}


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

            pieces = split_text(text)
            embeddings = embed_documents(pieces)
            replace_chunks(db, file.name, pieces, embeddings)
            print(f"{file.name}: {len(pieces)} chunks")


if __name__ == "__main__":
    main()
