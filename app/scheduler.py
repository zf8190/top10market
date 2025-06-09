from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

from app.services.archiving import archive_articles
from app.services.article_ai import (
    generate_daily_articles,
    update_articles_hourly
)
from app.services.feed_ingestion import update_feed

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
        # Genera nuovi articoli (basandosi su tutti i feed)
        await generate_daily_articles()
        # Aggiorna feed (legge feed nuovi e li inserisce)
        await update_feed()
    print(f"[{datetime.now()}] Daily morning job finished.")

async def hourly_update_job():
    print(f"[{datetime.now()}] Starting hourly update job...")
    # Aggiorna articoli (solo quelli con nuovi feed)
    await update_articles_hourly()
    # Aggiorna feed (legge nuovi feed)
    await update_feed()
    print(f"[{datetime.now()}] Hourly update job finished.")
