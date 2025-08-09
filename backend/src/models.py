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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func, text
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

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
    file_type = Column(String, nullable=False, default='html')
    embedding_type = Column(String, nullable=False, default='text')
    last_crawled = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_web_pages_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'lists': 100}),
        Index('idx_web_pages_url', 'url'),
        Index('idx_web_pages_textsearch', 'title', 'meta_description', 'content', postgresql_using='gin'),
    )

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    status = Column(String, nullable=False, default='pending')
    parameters = Column(JSON)
    result = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_jobs_status', 'status'),
    )

class JobBase(BaseModel):
    parameters: Optional[Dict[str, Any]] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class JobInDB(JobBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True