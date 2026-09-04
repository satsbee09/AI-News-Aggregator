from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "openai", "anthropic", "youtube"
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to Digest (1-to-1)
    digest: Mapped[Optional["Digest"]] = relationship("Digest", back_populates="article", uselist=False)

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, source='{self.source}', title='{self.title[:30]}...')>"


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_takeaways: Mapped[str] = mapped_column(Text, nullable=False)  # JSON or newline-separated bullet points
    category: Mapped[str] = mapped_column(String(100), default="General AI")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="digest")
    sent_logs: Mapped[list["SentLog"]] = relationship("SentLog", back_populates="digest")

    def __repr__(self) -> str:
        return f"<Digest(id={self.id}, article_id={self.article_id}, category='{self.category}')>"


class SentLog(Base):
    __tablename__ = "sent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_id: Mapped[int] = mapped_column(Integer, ForeignKey("digests.id"), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    digest: Mapped["Digest"] = relationship("Digest", back_populates="sent_logs")

    def __repr__(self) -> str:
        return f"<SentLog(id={self.id}, digest_id={self.digest_id}, recipient='{self.recipient}')>"
