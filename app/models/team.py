from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy.orm import relationship
from app.models.feed_per_team import feed_per_teams  # importa la tabella di join

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    logo_url = Column(String(255), nullable=True)

    # Un team ha un solo articolo (1:1)
    article = relationship("Article", back_populates="team", uselist=False)
    
    feeds = relationship("Feed", secondary=feed_per_teams, back_populates="teams")

