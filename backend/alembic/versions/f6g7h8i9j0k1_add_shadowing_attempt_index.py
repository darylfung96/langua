"""Add index on shadowing_attempts(session_id, phrase_id)

Revision ID: f6g7h8i9j0k1
Revises: e5f6a7b8c9d1
Create Date: 2026-03-14 01:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6a7b8c9d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite index on shadowing_attempts(session_id, phrase_id)."""
    op.create_index(
        'ix_shadowing_attempts_session_phrase', 'shadowing_attempts',
        ['session_id', 'phrase_id']
    )


def downgrade() -> None:
    """Remove the composite index."""
    op.drop_index('ix_shadowing_attempts_session_phrase', table_name='shadowing_attempts')
