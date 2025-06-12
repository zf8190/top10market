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
    generate_daily_article_for_team
)
from app.services.feed_ingestion import ingest_feeds
from app.services.article_ai import associate_feeds_to_teams
from app.models.team import Team

scheduler = AsyncIOScheduler()

def schedule_jobs():
    scheduler.add_job(
        archive_articles_job,
        trigger=CronTrigger(hour=7, minute=50),
        id="archive_articles_job",
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

async def archive_articles_job():
    print(f"[{datetime.now()}] Starting archive articles job...")
    async with async_session() as db:
        success = await archive_articles(db)
    print(f"[{datetime.now()}] Archive articles job finished.")

async def daily_morning_job():
    print(f"[{datetime.now()}] Starting daily morning job...")
    async with async_session() as db:
        await ingest_feeds(db)
        print(f"[{datetime.now()}] New feeds ingested successfully.")
        await associate_feeds_to_teams(db)
        await generate_daily_articles(db)
    print(f"[{datetime.now()}] Daily morning job finished.")

async def hourly_update_job():
    print(f"[{datetime.now()}] Starting hourly update job...")
    async with async_session() as db:
        await ingest_feeds(db)
        await associate_feeds_to_teams(db)
        print(f"[{datetime.now()}] New feeds ingested successfully.")

        result = await db.execute(select(Team).options(joinedload(Team.article)))
        teams = result.scalars().all()

        for team in teams:
            if team.article:
                await generate_daily_article_for_team(db, team)
            else:
                await update_hourly_articles(db, team)

    print(f"[{datetime.now()}] Hourly update job finished.")
