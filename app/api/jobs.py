from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
import asyncio

from app.scheduler import daily_morning_job, hourly_update_job, archive_job

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
async def run_archive_job(background_tasks: BackgroundTasks):
    """
    Avvia il job di archiviazione degli articoli in background.
    """
    try:
        background_tasks.add_task(archive_job)
        return {"status": "started", "job": "archive_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
