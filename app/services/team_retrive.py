from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import Team
from app.models.article import Article

class TeamService:
    @staticmethod
    async def get_teams_con_articoli(db: AsyncSession) -> List[Team]:
        stmt = (
            select(Team)
            .join(Article, Article.team_id == Team.id)
            .distinct()
        )
        result = await db.execute(stmt)
        teams = result.scalars().all()
        return teams

    @staticmethod
    async def get_teams_senza_articoli(db: AsyncSession) -> List[Team]:
        subquery = select(Article.id).where(Article.team_id == Team.id).exists()
        stmt = select(Team).where(~subquery)
        result = await db.execute(stmt)
        teams = result.scalars().all()
        return teams