# app/models/feed_per_team.py

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.models.base import Base

feed_per_teams = Table(
    "feed_per_teams",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("feed_id", Integer, ForeignKey("feeds.id"), primary_key=True),
)
