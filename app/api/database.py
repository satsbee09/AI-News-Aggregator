from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING
from app.config import settings

class MotorDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

motor_db = MotorDB()

async def connect_to_mongo():
    """Initializes Motor Async MongoDB client and ensures indexes on collections."""
    print(f"Connecting Motor async client to MongoDB ({settings.MONGODB_DB_NAME})...")
    motor_db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    motor_db.db = motor_db.client[settings.MONGODB_DB_NAME]
    
    # Ensure unique index on users.email
    users_col = motor_db.db["users"]
    await users_col.create_index([("email", ASCENDING)], unique=True)
    print("Motor async client connected and unique index on users.email ensured.")

async def close_mongo_connection():
    """Closes Motor async MongoDB connection."""
    if motor_db.client:
        motor_db.client.close()
        print("Motor async MongoDB connection closed.")

def get_motor_db() -> AsyncIOMotorDatabase:
    """Returns active Motor Async database instance."""
    if motor_db.db is None:
        raise RuntimeError("MongoDB async client is not connected. Call connect_to_mongo() first.")
    return motor_db.db

def get_users_collection() -> AsyncIOMotorCollection:
    """Returns users collection from active database."""
    return get_motor_db()["users"]
