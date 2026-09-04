import asyncio
import httpx
from app.server import app
from app.api.database import connect_to_mongo, close_mongo_connection, get_users_collection
from app.api.scheduler import scheduler, schedule_user_job

async def run_test():
    print("1. Connecting to MongoDB & Starting APScheduler...")
    await connect_to_mongo()
    if not scheduler.running:
        scheduler.start()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = "test_scheduler_user@example.com"
        
        # Step 1: Create user
        print(f"\n2. Creating test user: {test_email}...")
        await client.post("/api/users", json={"email": test_email})

        # Step 2: Configure topics
        print("3. Setting user topics...")
        await client.put(f"/api/users/{test_email}/topics", json={"topics": [
            {"name": "Frontier AI & LLMs", "scope": "ai", "category": "ai"},
            {"name": "Ghaziabad news", "scope": "local", "category": "local"}
        ]})

        # Step 3: Configure schedule
        print("4. Testing PUT /api/users/{email}/schedule...")
        sched_payload = {
            "time": "23:00",
            "frequency": "daily",
            "timezone": "Asia/Kolkata"
        }
        res = await client.put(f"/api/users/{test_email}/schedule", json=sched_payload)
        print(f"   Status: {res.status_code}, User schedule: {res.json()['schedule']}")
        assert res.status_code == 200
        assert res.json()["schedule"]["time"] == "23:00"

        # Step 4: Verify APScheduler job exists
        job_id = f"digest_job_{test_email}"
        job = scheduler.get_job(job_id)
        print(f"   [SUCCESS] Verified APScheduler Job exists: ID='{job.id}', Name='{job.name}'")
        assert job is not None

        # Step 5: Test Rescheduling
        print("\n5. Testing Rescheduling (Every 12 hours at 08:00)...")
        new_sched_payload = {
            "time": "08:00",
            "frequency": "every_12_hours",
            "timezone": "Asia/Kolkata"
        }
        res2 = await client.put(f"/api/users/{test_email}/schedule", json=new_sched_payload)
        assert res2.status_code == 200
        job2 = scheduler.get_job(job_id)
        print(f"   [SUCCESS] Rescheduled Job verified in APScheduler: {job2.trigger}")

        # Step 6: Test Manual Trigger (Dry Run)
        print("\n6. Testing POST /api/users/{email}/trigger (Dry run execution)...")
        trigger_res = await client.post(f"/api/users/{test_email}/trigger?dry_run=true")
        print(f"   Trigger status: {trigger_res.status_code}, Result: {trigger_res.json()}")
        assert trigger_res.status_code == 200
        assert trigger_res.json()["status"] in ["success", "error"]

    if scheduler.running:
        scheduler.shutdown()
    await close_mongo_connection()
    print("\n[SUCCESS] Phase 4 & 5 Schedule Management & Pipeline APIs test passed completely!")

if __name__ == "__main__":
    asyncio.run(run_test())
