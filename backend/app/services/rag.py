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
    # "I don't know" only when nothing in the context is relevant; otherwise answer directly,
    # even if the question uses other words than the document (e.g. "sick leaves" vs "sick days").
    rules = (
        "You answer employees' questions using only the company documents in the context below.\n"
        "- If the context contains information that answers the question, give that answer directly and name the policy it comes from, "
        "even if the question uses different words than the document (for example 'sick leaves' for 'sick days').\n"
        "- Do not start with 'I don't know' or say the context does not specify something when it contains the answer.\n"
        "- Only if nothing in the context is relevant to the question, reply: I don't know.\n"
        "- Do not add information that is not in the context.\n\n"
        f"Context:\n{context}"
    )
    return [
        {"role": "system", "content": rules},
        {"role": "user", "content": question},
    ]
