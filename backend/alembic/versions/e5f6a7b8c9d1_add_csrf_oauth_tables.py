"""Add csrf_tokens and oauth_codes tables

Revision ID: e5f6a7b8c9d1
Revises: d4e5f6a7b8c9
Create Date: 2026-03-14 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d1'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create csrf_tokens and oauth_codes tables."""
    # CSRF tokens table
    op.create_table(
        'csrf_tokens',
        sa.Column('token_hash', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_csrf_tokens_user_id'), 'csrf_tokens', ['user_id'])
    op.create_index(op.f('ix_csrf_tokens_expires_at'), 'csrf_tokens', ['expires_at'])

    # OAuth codes table
    op.create_table(
        'oauth_codes',
        sa.Column('code', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jwt_token', sa.Text, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_oauth_codes_expires_at'), 'oauth_codes', ['expires_at'])


def downgrade() -> None:
    """Drop csrf_tokens and oauth_codes tables."""
    op.drop_index(op.f('ix_oauth_codes_expires_at'), table_name='oauth_codes')
    op.drop_table('oauth_codes')
    op.drop_index(op.f('ix_csrf_tokens_user_id'), table_name='csrf_tokens')
    op.drop_index(op.f('ix_csrf_tokens_expires_at'), table_name='csrf_tokens')
    op.drop_table('csrf_tokens')
