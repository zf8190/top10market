import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.article import Article
from app.models.article_history import ArticleHistory

async def archive_articles(db: AsyncSession):
    today = datetime.date.today()
    archive_date = today - datetime.timedelta(days=1)

    result = await db.execute(select(Article))
    articles = result.scalars().all()

    for art in articles:
        archived = ArticleHistory(
            article_id=art.id,
            title=art.title,
            content=art.content,
            summary=art.summary,
            sources=art.sources,
            archived_at=datetime.datetime.combine(archive_date, datetime.time.min)  # facoltativo
        )
        db.add(archived)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

    # Elimina tutti gli articoli dopo il commit della copia
    await db.execute(delete(Article))
    await db.commit()
