"""Add structured_data column and feature flag

Revision ID: 905a6fc28d5c
Revises: 4d700d415774
Create Date: 2025-08-13 14:11:28.196693

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "905a6fc28d5c"
down_revision: Union[str, Sequence[str], None] = "4d700d415774"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the structured_data column to the web_pages table
    op.add_column(
        "web_pages",
        sa.Column(
            "structured_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Insert the new feature flag
    op.execute(
        """
        INSERT INTO feature_flags (name, is_enabled, description)
        VALUES ('structured_data_extraction', false, 'Enables the extraction of structured data from web pages.')
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the structured_data column from the web_pages table
    op.drop_column("web_pages", "structured_data")

    # Delete the feature flag
    op.execute("DELETE FROM feature_flags WHERE name = 'structured_data_extraction'")
