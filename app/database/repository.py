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

    # ==================== VECTOR EMBEDDING METHODS ====================

    def save_article_embedding(
        self,
        article_id: Any,
        digest_id: Any,
        topic: str,
        title: str,
        text: str,
        embedding: List[float],
        source_url: str = "",
        published_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Upserts an article vector embedding document in the article_embeddings collection."""
        art_oid = ObjectId(article_id) if isinstance(article_id, str) else article_id
        dig_oid = ObjectId(digest_id) if isinstance(digest_id, str) else digest_id
        
        doc = {
            "article_id": art_oid,
            "digest_id": dig_oid,
            "topic": topic,
            "title": title,
            "text": text,
            "embedding": embedding,
            "source_url": source_url,
            "published_at": published_at or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        self.db.article_embeddings.update_one(
            {"digest_id": dig_oid},
            {"$set": doc},
            upsert=True
        )
        return doc

    def get_unembedded_digests(self) -> List[Dict[str, Any]]:
        """Finds all digests that have not yet been embedded."""
        embedded_digest_ids = set(self.db.article_embeddings.distinct("digest_id"))
        pipeline = [
            {"$match": {"_id": {"$nin": list(embedded_digest_ids)}}},
            {
                "$lookup": {
                    "from": "articles",
                    "localField": "article_id",
                    "foreignField": "_id",
                    "as": "article"
                }
            },
            {"$unwind": {"path": "$article", "preserveNullAndEmptyArrays": True}}
        ]
        return list(self.db.digests.aggregate(pipeline))

    def vector_search(
        self,
        query_vector: List[float],
        limit: int = 6,
        topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes vector similarity search.
        First attempts MongoDB Atlas $vectorSearch aggregation stage.
        Gracefully falls back to in-memory cosine similarity ranking if search index is not yet active.
        """
        # 1. Try MongoDB Atlas $vectorSearch aggregation pipeline
        try:
            vector_search_stage: Dict[str, Any] = {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit
            }
            if topics and len(topics) > 0:
                vector_search_stage["filter"] = {"topic": {"$in": topics}}

            pipeline = [
                {"$vectorSearch": vector_search_stage},
                {
                    "$project": {
                        "_id": 1,
                        "article_id": 1,
                        "digest_id": 1,
                        "topic": 1,
                        "title": 1,
                        "text": 1,
                        "source_url": 1,
                        "published_at": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            results = list(self.db.article_embeddings.aggregate(pipeline))
            if results:
                return results
        except Exception as e:
            # Atlas Vector Search index might be initializing or running in standard search mode
            pass

        # 2. Resilient In-Memory Cosine Similarity Fallback
        from app.services.embedding_service import embedding_service
        match_filter: Dict[str, Any] = {}
        if topics and len(topics) > 0:
            match_filter["topic"] = {"$in": topics}

        candidates = list(self.db.article_embeddings.find(match_filter).limit(250))
        if not candidates:
            # If no matches with topic filter, fallback to general candidates
            candidates = list(self.db.article_embeddings.find({}).limit(250))

        scored = []
        for item in candidates:
            emb = item.get("embedding", [])
            if emb and len(emb) == len(query_vector):
                score = embedding_service.cosine_similarity(query_vector, emb)
                item["score"] = score
                scored.append(item)

        scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return scored[:limit]
