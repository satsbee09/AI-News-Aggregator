from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from app.config import settings

# Global MongoClient instance
client: MongoClient = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
db: Database = client[settings.MONGODB_DB_NAME]

def get_mongo_db() -> Database:
    """Returns the active MongoDB database instance."""
    return db

def init_mongo_db() -> None:
    """Initializes indexes for performance and deduplication."""
    database = get_mongo_db()
    
    # 1. Unique index on articles URL (ensures idempotent scraping)
    database.articles.create_index([("url", ASCENDING)], unique=True)
    
    # 2. Indexes on foreign keys / lookups
    database.digests.create_index([("article_id", ASCENDING)], unique=True)
    database.sent_logs.create_index([("digest_id", ASCENDING)])
    database.topics.create_index([("topic_name", ASCENDING)], unique=True)

    # 3. Seed default user topics if collection is empty
    seed_default_topics(database)

def seed_default_topics(database: Database) -> None:
    """Seeds starter multi-topic configuration if none exist."""
    if database.topics.count_documents({}) > 0:
        return

    default_topics = [
        {
            "topic_name": "Frontier AI & LLMs",
            "category": "ai",
            "scope": "international",
            "query": "Artificial Intelligence LLM OpenAI Anthropic DeepSeek",
            "location": "",
            "weight": 1.5,
            "active": True
        },
        {
            "topic_name": "Local Ghaziabad News",
            "category": "local",
            "scope": "local",
            "query": "Ghaziabad",
            "location": "Ghaziabad, India",
            "weight": 1.2,
            "active": True
        },
        {
            "topic_name": "National News & Politics",
            "category": "national",
            "scope": "national",
            "query": "India politics economy policy",
            "location": "India",
            "weight": 1.0,
            "active": True
        },
        {
            "topic_name": "Global Geopolitics",
            "category": "international",
            "scope": "international",
            "query": "world politics diplomacy global economy",
            "location": "",
            "weight": 1.0,
            "active": True
        },
        {
            "topic_name": "Cricket & Sports",
            "category": "sports",
            "scope": "national",
            "query": "cricket match India tournament",
            "location": "India",
            "weight": 0.9,
            "active": True
        },
        {
            "topic_name": "Delhi NCR Weather",
            "category": "weather",
            "scope": "weather",
            "query": "Delhi",
            "location": "Delhi, India",
            "weight": 1.0,
            "active": True
        }
    ]

    for t in default_topics:
        database.topics.update_one({"topic_name": t["topic_name"]}, {"$setOnInsert": t}, upsert=True)
    print("   [DB] Seeded default multi-topic preferences in MongoDB.")
