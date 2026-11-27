from sqlalchemy import Computed, Index, String, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR


# message class
class Message(Base):
    __tablename__ = "messages"
    # GIN index on the search column: finds matching messages without reading every row
    __table_args__ = (Index("ix_messages_search_vector", "search_vector", postgresql_using="gin"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    # Full-text search version of `content` (words reduced to their stem, e.g. "holidays" -> "holiday").
    # Postgres fills it in by itself on every insert/update (GENERATED ... STORED); the app never writes it.
    # deferred: not loaded when messages are read normally, only used inside search queries.
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True), deferred=True
    )

    # messages belong to a conversation
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

