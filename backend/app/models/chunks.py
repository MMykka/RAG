from sqlalchemy import  Index, String, DateTime, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base
from pgvector.sqlalchemy import Vector

class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__= (UniqueConstraint("source", "chunk_index"), Index("ix_chunks_embedding", "embedding", postgresql_using="hnsw",
      postgresql_ops={"embedding": "vector_cosine_ops"}))

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())