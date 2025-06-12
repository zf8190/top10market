from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.db import async_session
from app.services.archiving import archive_articles
from app.services.article_ai import (
    generate_daily_articles,
    update_hourly_articles,
    associate_feeds_to_teams
)
from app.services.feed_ingestion import ingest_feeds
from app.models.team import Team


scheduler = AsyncIOScheduler()

def schedule_jobs():
    scheduler.add_job(
        archive_job,
        trigger=CronTrigger(hour=7, minute=50),
        id="archive_job",
        replace_existing=True,
    )
    scheduler.add_job(
        daily_morning_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_morning_job",
        replace_existing=True,
    )
    scheduler.add_job(
        hourly_update_job,
        trigger=CronTrigger(hour="9-21", minute=0),
        id="hourly_update_job",
        replace_existing=True,
    )

async def archive_job():
    print(f"[{datetime.now()}] Starting archive job...")
    async with async_session() as db:
        success = await archive_articles(db)
    print(f"[{datetime.now()}] Archive job finished.")

async def daily_morning_job():
    print(f"[{datetime.now()}] Starting daily morning job...")
    async with async_session() as db:
        await ingest_feeds(db)
        print(f"[{datetime.now()}] New feeds ingested successfully.")
        await associate_feeds_to_teams(db)

        await generate_daily_articles(db)  # CORRETTO

    print(f"[{datetime.now()}] Daily morning job finished.")


async def hourly_update_job():
    print(f"[{datetime.now()}] Starting hourly update job...")
    async with async_session() as db:
        # 1. Ingest feeds
        await ingest_feeds(db)
        # 2. Associate feeds to teams
        await associate_feeds_to_teams(db)
        print(f"[{datetime.now()}] New feeds ingested and associated successfully.")

        # 3. Cicla su tutti i team
        result = await db.execute(select(Team).options(joinedload(Team.articles)))
        teams = result.scalars().all()

        for team in teams:
            # Se esiste almeno un articolo associato al team
            if team.articles and len(team.articles) > 0:
                # genera articoli giornalieri completi per quel team
                await generate_daily_articles(db, team=team)
            else:
                # aggiorna o crea articoli orari per quel team
                await update_hourly_articles(db, team=team)

    print(f"[{datetime.now()}] Hourly update job finished.")
