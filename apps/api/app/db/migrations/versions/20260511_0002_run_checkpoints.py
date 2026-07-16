"""Add durable run checkpoints."""

from alembic import op
import sqlalchemy as sa


revision = "20260511_0002"
down_revision = "20260511_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_checkpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("checkpoint_type", sa.String(length=32), nullable=False),
        sa.Column("runtime_status", sa.String(length=32), nullable=False),
        sa.Column("sim_rate", sa.Float(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_run_checkpoints_run_id"),
        "run_checkpoints",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_run_checkpoints_run_id"), table_name="run_checkpoints")
    op.drop_table("run_checkpoints")
