import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.api.schemas import ScheduleSettings
from app.api.database import get_users_collection
from app.api.services.user_pipeline import run_user_pipeline

scheduler = AsyncIOScheduler(timezone=pytz.utc)

async def _job_callback(email: str):
    """Callback triggered by APScheduler to run the personalized pipeline."""
    try:
        print(f"[SCHEDULER TRIGGER] Firing scheduled job for {email}...")
        await run_user_pipeline(email=email)
    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to run pipeline for {email}: {e}")

def schedule_user_job(email: str, schedule: ScheduleSettings):
    """Registers or reschedules a user's automated digest job in APScheduler."""
    job_id = f"digest_job_{email.lower().strip()}"
    tz_str = schedule.timezone or "Asia/Kolkata"
    
    try:
        user_tz = pytz.timezone(tz_str)
    except Exception:
        user_tz = pytz.timezone("Asia/Kolkata")

    # Parse HH:MM
    time_parts = schedule.time.split(":")
    hour = int(time_parts[0]) if len(time_parts) > 0 and time_parts[0].isdigit() else 7
    minute = int(time_parts[1]) if len(time_parts) > 1 and time_parts[1].isdigit() else 30

    if schedule.frequency == "every_6_hours":
        trigger = IntervalTrigger(hours=6, timezone=user_tz)
    elif schedule.frequency == "every_12_hours":
        trigger = IntervalTrigger(hours=12, timezone=user_tz)
    else:
        # Default: Daily at specified hour:minute
        trigger = CronTrigger(hour=hour, minute=minute, timezone=user_tz)

    scheduler.add_job(
        _job_callback,
        trigger=trigger,
        id=job_id,
        args=[email],
        replace_existing=True,
        name=f"Digest for {email}"
    )
    print(f"[SCHEDULER] Scheduled job '{job_id}' ({schedule.frequency} at {hour:02d}:{minute:02d} {tz_str})")

async def init_scheduler_jobs():
    """Loads all saved user schedules from MongoDB and populates APScheduler jobs on startup."""
    try:
        users_col = get_users_collection()
        cursor = users_col.find({"schedule": {"$exists": True}})
        users = await cursor.to_list(length=1000)
        
        count = 0
        for u in users:
            email = u.get("email")
            sched_dict = u.get("schedule", {})
            if email and sched_dict:
                settings_obj = ScheduleSettings(**sched_dict)
                schedule_user_job(email, settings_obj)
                count += 1
                
        print(f"[SCHEDULER] Loaded and registered {count} user job(s) from database.")
    except Exception as e:
        print(f"[SCHEDULER INIT ERROR] Could not load user jobs: {e}")
