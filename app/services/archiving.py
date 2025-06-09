# Daily archiving logicimport datetime
from sqlalchemy.orm import Session
from app.models.article import Article
from app.models.article_history import ArticleHistory

def archive_articles(db: Session):
    """
    Archivia tutti gli articoli correnti nella tabella ArticleHistory.
    Se l’archiviazione va a buon fine, elimina gli articoli correnti.
    """
    today = datetime.date.today()
    archive_date = today - datetime.timedelta(days=1)

    articles = db.query(Article).all()

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
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    # Solo se commit ha avuto successo:
    db.query(Article).delete()
    db.commit()
