"""add_is_admin_to_users

Revision ID: 064a312d9b44
Revises: d98bb0db7e33
Create Date: 2026-05-31 00:39:57.818712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '064a312d9b44'
down_revision: Union[str, Sequence[str], None] = 'd98bb0db7e33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_admin' not in columns:
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_admin' in columns:
        op.drop_column('users', 'is_admin')
