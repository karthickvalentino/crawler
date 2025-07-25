"""Create web_pages table

Revision ID: 939d487ab146
Revises: 
Create Date: 2025-07-25 12:32:50.959298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '939d487ab146'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.create_table(
        'web_pages',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_tags', sa.JSON(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('last_crawled', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index('idx_web_pages_embedding', 'web_pages', ['embedding'], unique=False, postgresql_using='ivfflat', postgresql_with={'lists': 100})
    op.create_index('idx_web_pages_url', 'web_pages', ['url'], unique=False)
    op.create_index(
        'idx_web_pages_textsearch',
        'web_pages',
        [sa.text("to_tsvector('english', coalesce(title, '') || ' ' || coalesce(meta_description, '') || ' ' || coalesce(content, ''))")],
        unique=False,
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_web_pages_textsearch', table_name='web_pages')
    op.drop_index('idx_web_pages_url', table_name='web_pages')
    op.drop_index('idx_web_pages_embedding', table_name='web_pages')
    op.drop_table('web_pages')
    op.execute("DROP EXTENSION IF EXISTS vector;")
