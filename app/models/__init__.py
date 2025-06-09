from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .team import Team
from .feed import Feed
from .article import Article
from .article_history import ArticleHistory