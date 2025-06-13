from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class ArticleHistory(Base):
    __tablename__ = "article_history"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)  # Fonti consultate
    archived_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
