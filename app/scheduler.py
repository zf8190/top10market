from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

from app.services.archiving import archive_articles
from app.services.article_ai import (
    generate_article_content,
    update_article_content
)
from app.services.feed_ingestion import ingest_feeds

scheduler = AsyncIOScheduler()

def schedule_jobs():
    # Ogni giorno alle 08:00: archivio articoli, genero nuovi e aggiorno feed
    scheduler.add_job(
        daily_morning_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_morning_job",
        replace_existing=True,
    )

    # Ogni ora dalle 9 alle 21: aggiorno articoli e feed
    scheduler.add_job(
        hourly_update_job,
        trigger=CronTrigger(hour="9-21", minute=0),
        id="hourly_update_job",
        replace_existing=True,
    )

async def daily_morning_job():
    print(f"[{datetime.now()}] Starting daily morning job...")

    # Archivia articoli precedenti
    success = await archive_articles()
    if success:
        # Ingest nuovi feed
        await ingest_feeds()
        print(f"[{datetime.now()}] New feeds ingested successfully.")

        # Genera nuovi articoli
        await generate_article_content()

    print(f"[{datetime.now()}] Daily morning job finished.")

async def hourly_update_job():
    print(f"[{datetime.now()}] Starting hourly update job...")

    # Ingest nuovi feed
    await ingest_feeds()
    print(f"[{datetime.now()}] New feeds ingested successfully.")

    # Aggiorna articoli
    await update_article_content()

    print(f"[{datetime.now()}] Hourly update job finished.")
