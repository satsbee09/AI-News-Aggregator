'''from datetime import datetime
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
        return log_entry '''

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from app.database.mongo import get_mongo_db

class MongoRepository:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_mongo_db()

    # ==================== TOPIC METHODS ====================

    def get_active_topics(self) -> List[Dict[str, Any]]:
        """Returns all active user topics."""
        return list(self.db.topics.find({"active": True}))

    # ==================== ARTICLE METHODS ====================

    def save_article(
        self,
        title: str,
        url: str,
        source: str,
        raw_content: str,
        category: str = "general",
        topic_name: str = "General News",
        published_at: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Idempotently saves article using unique index on URL."""
        article_doc = {
            "title": title,
            "url": url,
            "source": source,
            "category": category,
            "topic_name": topic_name,
            "raw_content": raw_content,
            "published_at": published_at or datetime.now(timezone.utc),
            "scraped_at": datetime.now(timezone.utc)
        }
        try:
            result = self.db.articles.insert_one(article_doc)
            article_doc["_id"] = result.inserted_id
            return article_doc
        except DuplicateKeyError:
            return None  # Duplicate URL, safely ignored

    def get_unprocessed_articles(self) -> List[Dict[str, Any]]:
        """Returns articles that do not have a corresponding digest yet."""
        # Find all article IDs that already have a digest
        digested_article_ids = set(self.db.digests.distinct("article_id"))
        
        # Query articles whose _id is not in digested_article_ids
        unprocessed = list(self.db.articles.find({
            "_id": {"$nin": list(digested_article_ids)}
        }))
        return unprocessed

    # ==================== DIGEST METHODS ====================

    def save_digest(
        self,
        article_id: Any,
        summary: str,
        key_takeaways: str,
        category: str = "general",
        topic_name: str = "General News"
    ) -> Dict[str, Any]:
        """Saves LLM digest document."""
        digest_doc = {
            "article_id": ObjectId(article_id) if isinstance(article_id, str) else article_id,
            "summary": summary,
            "key_takeaways": key_takeaways,
            "category": category,
            "topic_name": topic_name,
            "created_at": datetime.now(timezone.utc)
        }
        result = self.db.digests.insert_one(digest_doc)
        digest_doc["_id"] = result.inserted_id
        return digest_doc

    def get_unsent_digests(self) -> List[Dict[str, Any]]:
        """Returns digests that have not been sent in sent_logs yet."""
        sent_digest_ids = set(self.db.sent_logs.distinct("digest_id"))
        
        pipeline = [
            {"$match": {"_id": {"$nin": list(sent_digest_ids)}}},
            {
                "$lookup": {
                    "from": "articles",
                    "localField": "article_id",
                    "foreignField": "_id",
                    "as": "article"
                }
            },
            {"$unwind": "$article"}
        ]
        return list(self.db.digests.aggregate(pipeline))

    # ==================== SENT LOG METHODS ====================

    def log_sent_digest(self, digest_id: Any, recipient: str) -> Dict[str, Any]:
        """Records delivered digest to prevent duplicate emails."""
        log_doc = {
            "digest_id": ObjectId(digest_id) if isinstance(digest_id, str) else digest_id,
            "recipient": recipient,
            "sent_at": datetime.now(timezone.utc)
        }
        result = self.db.sent_logs.insert_one(log_doc)
        log_doc["_id"] = result.inserted_id
        return log_doc
