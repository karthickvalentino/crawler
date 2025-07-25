from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class WebPage(Base):
    __tablename__ = 'web_pages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False, unique=True)
    domain = Column(Text, nullable=False)
    title = Column(Text)
    meta_description = Column(Text)
    meta_tags = Column(JSON)
    content = Column(Text)
    embedding = Column(Vector(1024))
    last_crawled = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_web_pages_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'lists': 100}),
        Index('idx_web_pages_url', 'url'),
        Index('idx_web_pages_textsearch', 'title', 'meta_description', 'content', postgresql_using='gin'),
    )
