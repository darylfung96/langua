"""composite user_id+created_at indexes for pagination

Revision ID: a1c4e8d3f9b2
Revises: 80907fa4fdbf
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1c4e8d3f9b2'
down_revision: Union[str, Sequence[str], None] = '80907fa4fdbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite (user_id, created_at) indexes to improve paginated list queries."""
    with op.batch_alter_table('stories', schema=None) as batch_op:
        batch_op.create_index('ix_stories_user_created', ['user_id', 'created_at'])

    with op.batch_alter_table('lyrics', schema=None) as batch_op:
        batch_op.create_index('ix_lyrics_user_created', ['user_id', 'created_at'])

    with op.batch_alter_table('visuals', schema=None) as batch_op:
        batch_op.create_index('ix_visuals_user_created', ['user_id', 'created_at'])

    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.create_index('ix_resources_user_created', ['user_id', 'created_at'])


def downgrade() -> None:
    """Drop composite indexes."""
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.drop_index('ix_resources_user_created')

    with op.batch_alter_table('visuals', schema=None) as batch_op:
        batch_op.drop_index('ix_visuals_user_created')

    with op.batch_alter_table('lyrics', schema=None) as batch_op:
        batch_op.drop_index('ix_lyrics_user_created')

    with op.batch_alter_table('stories', schema=None) as batch_op:
        batch_op.drop_index('ix_stories_user_created')
