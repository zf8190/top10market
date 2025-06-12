from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
import asyncio

from app.scheduler import daily_morning_job, hourly_update_job, archive_articles_job

router = APIRouter()

@router.get("/jobs/daily-morning")
async def run_daily_morning_job(background_tasks: BackgroundTasks):
    """
    Avvia il job schedulato giornaliero in background.
    """
    try:
        background_tasks.add_task(daily_morning_job)
        return {"status": "started", "job": "daily_morning_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/hourly-update")
async def run_hourly_update_job(background_tasks: BackgroundTasks):
    """
    Avvia il job schedulato orario in background.
    """
    try:
        background_tasks.add_task(hourly_update_job)
        return {"status": "started", "job": "hourly_update_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/archive")
async def archive_articles_job():
    print(f"[{datetime.now()}] Starting archive articles job...")
    async with async_session() as db:
        success = await archive_articles(db)
    print(f"[{datetime.now()}] Archive articles job finished.")
