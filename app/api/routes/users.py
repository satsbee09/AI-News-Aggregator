from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.api.database import get_users_collection
from app.api.schemas import (
    UserCreateRequest,
    UserTopicsUpdateRequest,
    UserResponse,
    TopicItem,
    ScheduleSettings
)

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def create_or_get_user(payload: UserCreateRequest):
    """Creates a new user or returns existing user by email (upsert)."""
    users_col = get_users_collection()
    email = payload.email.lower().strip()
    
    existing = await users_col.find_one({"email": email})
    now = datetime.now(timezone.utc)
    
    if existing:
        return UserResponse(
            email=existing["email"],
            topics=existing.get("topics", []),
            schedule=existing.get("schedule", ScheduleSettings().model_dump()),
            created_at=existing.get("created_at"),
            updated_at=existing.get("updated_at")
        )
    
    # Default initial topics
    default_topics = [
        {"name": "Frontier AI & LLMs", "scope": "ai", "category": "ai"},
        {"name": "Local News", "scope": "local", "category": "local"},
        {"name": "National Politics", "scope": "national", "category": "national"},
        {"name": "Cricket & Sports", "scope": "sports", "category": "sports"}
    ]
    
    new_user_doc = {
        "email": email,
        "topics": default_topics,
        "schedule": ScheduleSettings().model_dump(),
        "created_at": now,
        "updated_at": now
    }
    
    await users_col.insert_one(new_user_doc)
    return UserResponse(
        email=email,
        topics=[TopicItem(**t) for t in default_topics],
        schedule=ScheduleSettings(),
        created_at=now,
        updated_at=now
    )

@router.get("/{email}", response_model=UserResponse)
async def get_user_profile(email: str):
    """Fetches user profile, selected topics, and schedule settings."""
    users_col = get_users_collection()
    email_clean = email.lower().strip()
    
    user = await users_col.find_one({"email": email_clean})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email_clean}' not found."
        )
    
    return UserResponse(
        email=user["email"],
        topics=user.get("topics", []),
        schedule=user.get("schedule", ScheduleSettings().model_dump()),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )

@router.put("/{email}/topics", response_model=UserResponse)
async def update_user_topics(email: str, payload: UserTopicsUpdateRequest):
    """Updates user's selected topics (predefined + custom). Requires at least 1 topic."""
    if not payload.topics:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one topic must be selected."
        )
    
    users_col = get_users_collection()
    email_clean = email.lower().strip()
    
    # Normalize topics: default scope to 'general' if missing, set category accordingly
    clean_topics = []
    for t in payload.topics:
        topic_dict = t.model_dump()
        if not topic_dict.get("scope"):
            topic_dict["scope"] = "general"
        if not topic_dict.get("category"):
            topic_dict["category"] = topic_dict["scope"]
        clean_topics.append(topic_dict)
    
    now = datetime.now(timezone.utc)
    res = await users_col.find_one_and_update(
        {"email": email_clean},
        {"$set": {"topics": clean_topics, "updated_at": now}},
        return_document=True
    )
    
    if not res:
        # Create user if doesn't exist
        new_doc = {
            "email": email_clean,
            "topics": clean_topics,
            "schedule": ScheduleSettings().model_dump(),
            "created_at": now,
            "updated_at": now
        }
        await users_col.insert_one(new_doc)
        res = new_doc
        
    return UserResponse(
        email=res["email"],
        topics=res.get("topics", []),
        schedule=res.get("schedule", ScheduleSettings().model_dump()),
        created_at=res.get("created_at"),
        updated_at=res.get("updated_at")
    )
