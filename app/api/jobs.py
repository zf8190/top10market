from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio

from app.scheduler import (
    archive_articles_job,
    process_unprocessed_feeds_job,
    ingest_and_associate_job
)

router = APIRouter()

@router.get("/jobs/archive")
async def run_archive_articles_job():
    try:
        asyncio.create_task(archive_articles_job())
        return {"status": "started", "job": "archive_articles_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/process-feeds")
async def run_process_unprocessed_feeds_job():
    try:
        asyncio.create_task(process_unprocessed_feeds_job())
        return {"status": "started", "job": "process_unprocessed_feeds_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/ingest-associate")
async def run_ingest_and_associate_job():
    try:
        asyncio.create_task(ingest_and_associate_job())
        return {"status": "started", "job": "ingest_and_associate_job", "started_at": str(datetime.utcnow())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
