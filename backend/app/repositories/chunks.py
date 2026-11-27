from app.models.chunks import Chunk
from sqlalchemy import func
from sqlalchemy.orm import Session


def replace_chunks(db: Session, source: str, pieces: list[str], embeddings: list[list[float]]) -> None:
    db.query(Chunk).filter(Chunk.source == source).delete()
    for index, (content, embedding) in enumerate(zip(pieces, embeddings)):
        chunk = Chunk(source=source, chunk_index=index, content=content, embedding=embedding)
        db.add(chunk)
    db.commit()
    
def search_chunks(db: Session, embedding: list[float], limit: int) -> list[Chunk]:
    return db.query(Chunk).order_by(Chunk.embedding.cosine_distance(embedding)).limit(limit).all()


# The documents in the knowledge base: one row per file (chunks.source), in one query
def list_documents(db: Session) -> list[dict]:
    rows = (
        db.query(
            Chunk.source,
            func.count(Chunk.id),
            func.max(Chunk.created_at),
            func.sum(func.octet_length(Chunk.content)),
        )
        .group_by(Chunk.source)
        .order_by(Chunk.source)
        .all()
    )
    return [
        {"name": source, "chunks": count, "added": added, "size_bytes": int(size or 0)}
        for source, count, added, size in rows
    ]

    