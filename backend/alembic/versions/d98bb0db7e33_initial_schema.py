"""initial_schema

Revision ID: d98bb0db7e33
Revises:
Create Date: 2026-05-20 16:12:33.977051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "d98bb0db7e33"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("stripe_account_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "spots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_spots_lat", "spots", ["lat"])
    op.create_index("ix_spots_lng", "spots", ["lng"])
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("spot_id", sa.Uuid(), nullable=False),
        sa.Column("filmer_id", sa.Uuid(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("thumbnail_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["filmer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["spot_id"], ["spots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "clips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("r2_raw_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("stream_uid", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clips_session_id", "clips", ["session_id"])
    op.create_index("ix_clips_captured_at", "clips", ["captured_at"])
    op.create_table(
        "purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("stripe_session_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_session_id"),
    )
    op.create_table(
        "stripe_events",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("stripe_events")
    op.drop_table("purchases")
    op.drop_index("ix_clips_captured_at", table_name="clips")
    op.drop_index("ix_clips_session_id", table_name="clips")
    op.drop_table("clips")
    op.drop_table("sessions")
    op.drop_index("ix_spots_lng", table_name="spots")
    op.drop_index("ix_spots_lat", table_name="spots")
    op.drop_table("spots")
    op.drop_table("users")
