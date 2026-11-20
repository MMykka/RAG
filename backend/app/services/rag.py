from sqlalchemy.orm import Session
from app.config import settings
from app.models.chunks import Chunk
from app.repositories.chunks import search_chunks
from app.services.llm import embed_query





def retrieve_chunks(db: Session, question: str) -> list[Chunk]:
    embedding = embed_query(question)
    chunks = search_chunks(db, embedding, limit=settings.rag_top_k)
    return chunks