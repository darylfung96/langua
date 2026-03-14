"""add account lockout fields to users

Revision ID: c3f7a1d9e5b8
Revises: a1c4e8d3f9b2
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f7a1d9e5b8'
down_revision: Union[str, Sequence[str], None] = 'a1c4e8d3f9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column(
        'failed_login_attempts',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))
    op.add_column('users', sa.Column(
        'locked_until',
        sa.DateTime(),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
