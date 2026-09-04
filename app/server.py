import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.database import connect_to_mongo, close_mongo_connection, get_motor_db
from app.api.scheduler import scheduler, init_scheduler_jobs

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB via Motor
    await connect_to_mongo()
    
    # Start APScheduler & load jobs
    scheduler.start()
    await init_scheduler_jobs()
    print("[SERVER] APScheduler started successfully.")
    
    yield
    
    # Shutdown: Stop scheduler & close MongoDB
    if scheduler.running:
        scheduler.shutdown()
        print("[SERVER] APScheduler shut down.")
    await close_mongo_connection()

app = FastAPI(
    title="Universal News Aggregator API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes.users import router as users_router
from app.api.routes.news import router as news_router
from app.api.routes.schedule import router as schedule_router
from app.api.routes.internal import router as internal_router

app.include_router(users_router)
app.include_router(news_router)
app.include_router(schedule_router)
app.include_router(internal_router)


@app.get("/api/health")
async def health_check():
    """Health check route to verify FastAPI and MongoDB connectivity."""
    db = get_motor_db()
    pong = await db.command("ping")
    return {
        "status": "healthy",
        "mongodb": "connected" if pong.get("ok") == 1.0 else "disconnected",
        "scheduler": "running" if scheduler.running else "stopped",
        "service": "Universal News Aggregator API"
    }

# Serve React static build if built
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static_frontend")
