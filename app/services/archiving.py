import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.article import Article
from app.models.article_history import ArticleHistory

async def archive_articles(db: AsyncSession):
    """
    Archivia tutti gli articoli correnti nella tabella ArticleHistory.
    Se l’archiviazione va a buon fine, elimina gli articoli correnti.
    """
    today = datetime.date.today()
    archive_date = today - datetime.timedelta(days=1)

    result = await db.execute(select(Article))
    articles = result.scalars().all()

    for art in articles:
        archived = ArticleHistory(
            team_id=art.team_id,
            title=art.title,
            content=art.content,
            summary=art.summary,
            last_updated=art.last_updated,
            archived_date=archive_date,
            sources=art.sources
        )
        db.add(archived)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

    # Solo se commit ha avuto successo:
    await db.execute(delete(Article))
    await db.commit()
