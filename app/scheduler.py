from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.db import async_session
from app.services.article_ai import process_unprocessed_feeds
from app.services.feed_ingestion import ingest_feeds
from app.services.article_ai import associate_feeds_to_teams
from app.models.team import Team

scheduler = AsyncIOScheduler()

def schedule_jobs():
    scheduler.add_job(
        process_unprocessed_feeds,
        trigger=CronTrigger(minute="15,45", hour="8-22"),
        id="process_unprocessed_feeds_job",
        replace_existing=True,
    )
    scheduler.add_job(
        ingest_and_associate_job,
        trigger=CronTrigger(minute="0,30", hour="8-22"),
        id="ingest_and_associate_job",
        replace_existing=True,
    )

async def process_unprocessed_feeds_job():
    print(f"[{datetime.now()}] Starting hourly update job...")
    async with async_session() as db:
        await process_unprocessed_feeds(db)
        print(f"[{datetime.now()}] New feed processed successfully.")
    print(f"[{datetime.now()}] Process unprocessed job finished.")

async def ingest_and_associate_job():
    print(f"[{datetime.now()}] Starting ingest and associate job...")
    async with async_session() as db:
        await ingest_feeds(db)
        print(f"[{datetime.now()}] New feeds ingested successfully.")
        await associate_feeds_to_teams(db)
        print(f"[{datetime.now()}] Feeds associated to teams successfully.")
    print(f"[{datetime.now()}] Ingest and associate job finished.")
