from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.api.database import get_users_collection
from app.api.schemas import ScheduleSettings, UserResponse
from app.api.scheduler import schedule_user_job
from app.api.services.user_pipeline import run_user_pipeline

router = APIRouter(prefix="/api/users", tags=["Schedule"])

@router.put("/{email}/schedule", response_model=UserResponse)
async def update_user_schedule(email: str, payload: ScheduleSettings):
    """Updates user's delivery schedule settings and registers/reschedules their APScheduler job."""
    users_col = get_users_collection()
    email_clean = email.lower().strip()
    
    now = datetime.now(timezone.utc)
    res = await users_col.find_one_and_update(
        {"email": email_clean},
        {"$set": {"schedule": payload.model_dump(), "updated_at": now}},
        return_document=True
    )
    
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email_clean}' not found. Please create user first."
        )
        
    # Register/Reschedule APScheduler job
    schedule_user_job(email_clean, payload)
    
    return UserResponse(
        email=res["email"],
        topics=res.get("topics", []),
        schedule=res.get("schedule", ScheduleSettings().model_dump()),
        created_at=res.get("created_at"),
        updated_at=res.get("updated_at")
    )

@router.post("/{email}/trigger")
async def trigger_user_digest_now(email: str, dry_run: bool = False):
    """Manually triggers the personalized digest pipeline for a user immediately."""
    email_clean = email.lower().strip()
    result = await run_user_pipeline(email=email_clean, dry_run=dry_run)
    return result
