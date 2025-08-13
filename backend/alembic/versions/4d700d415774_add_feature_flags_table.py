"""Add feature_flags table

Revision ID: 4d700d415774
Revises: 5027f84c0e0f
Create Date: 2025-08-13 13:14:18.383045

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d700d415774"
down_revision: Union[str, Sequence[str], None] = "5027f84c0e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the feature_flags table
    feature_flags_table = op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Insert the initial feature flags
    op.bulk_insert(
        feature_flags_table,
        [
            {
                "name": "chat_ui",
                "is_enabled": True,
                "description": "Enables the interactive chat UI feature.",
            },
            {
                "name": "multimodal_embeddings",
                "is_enabled": True,
                "description": "Enables the generation of embeddings for images.",
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the feature_flags table
    op.drop_table("feature_flags")
