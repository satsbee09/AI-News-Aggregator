from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models import Article, Digest, SentLog

class Repository:
    def __init__(self, session: Session):
        self.session = session

    # ==================== ARTICLE METHODS ====================

    def save_article(
        self,
        title: str,
        url: str,
        source: str,
        raw_content: str,
        published_at: Optional[datetime] = None
    ) -> Optional[Article]:
        """Saves article if URL does not already exist (idempotent insert)."""
        existing = self.session.scalar(select(Article).where(Article.url == url))
        if existing:
            return None  # Already exists, skip duplicate

        article = Article(
            title=title,
            url=url,
            source=source,
            raw_content=raw_content,
            published_at=published_at
        )
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def get_unprocessed_articles(self) -> List[Article]:
        """Returns all articles that don't have a summary digest yet."""
        # Find articles where digest is None (left outer join / outerjoin)
        stmt = select(Article).outerjoin(Digest).where(Digest.id.is_(None))
        return list(self.session.scalars(stmt).all())

    # ==================== DIGEST METHODS ====================

    def save_digest(
        self,
        article_id: int,
        summary: str,
        key_takeaways: str,
        category: str = "General AI"
    ) -> Digest:
        """Saves a generated LLM digest for an article."""
        digest = Digest(
            article_id=article_id,
            summary=summary,
            key_takeaways=key_takeaways,
            category=category
        )
        self.session.add(digest)
        self.session.commit()
        self.session.refresh(digest)
        return digest

    def get_unsent_digests(self) -> List[Digest]:
        """Returns digests that have not been logged in sent_logs yet."""
        stmt = select(Digest).outerjoin(SentLog).where(SentLog.id.is_(None))
        return list(self.session.scalars(stmt).all())

    # ==================== SENT LOG METHODS ====================

    def log_sent_digest(self, digest_id: int, recipient: str) -> SentLog:
        """Records that a digest has been sent to prevent resending."""
        log_entry = SentLog(digest_id=digest_id, recipient=recipient)
        self.session.add(log_entry)
        self.session.commit()
        self.session.refresh(log_entry)
        return log_entry
