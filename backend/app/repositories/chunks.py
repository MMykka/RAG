from app.models.chunks import Chunk
from sqlalchemy.orm import Session


def replace_chunks(db: Session, source: str, pieces: list[str], embeddings: list[list[float]]) -> None:
    db.query(Chunk).filter(Chunk.source == source).delete()
    for index, (content, embedding) in enumerate(zip(pieces, embeddings)):
        chunk = Chunk(source=source, chunk_index=index, content=content, embedding=embedding)
        db.add(chunk)
    db.commit()