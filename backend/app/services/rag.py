from sqlalchemy.orm import Session
from app.config import settings
from app.models.chunks import Chunk
from app.repositories.chunks import search_chunks
from app.services.llm import embed_query


def retrieve_chunks(db: Session, question: str) -> list[Chunk]:
    embedding = embed_query(question)
    chunks = search_chunks(db, embedding, limit=settings.rag_top_k)
    return chunks


def build_prompt(question: str, chunks: list[Chunk]) -> list[dict]:
    # No documents found: send the question on its own, so the chat still works.
    if not chunks:
        return [{"role": "user", "content": question}]

    # The rules and the document pieces go in a "system" message, the question stays a plain
    # "user" message. When chat history is added later, the earlier messages go in between
    # and the rules stay in one place.
    context = "\n\n".join([f"Source: {chunk.source}\nContent: {chunk.content}" for chunk in chunks])
    rules = f"Answer the question based on the context below. If the answer is not contained within the context, say 'I don't know'.\n\nContext:\n{context}"
    return [
        {"role": "system", "content": rules},
        {"role": "user", "content": question},
    ]
