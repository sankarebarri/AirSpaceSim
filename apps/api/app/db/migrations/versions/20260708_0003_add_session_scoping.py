"""Add session scoping to runs and scenarios."""

from alembic import op
import sqlalchemy as sa


revision = "20260708_0003"
down_revision = "20260511_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column(
            "session_id", sa.String(length=64), nullable=False, server_default="legacy"
        ),
    )
    op.create_index(
        op.f("ix_scenarios_session_id"), "scenarios", ["session_id"], unique=False
    )
    op.add_column(
        "runs",
        sa.Column(
            "session_id", sa.String(length=64), nullable=False, server_default="legacy"
        ),
    )
    op.create_index(op.f("ix_runs_session_id"), "runs", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_runs_session_id"), table_name="runs")
    op.drop_column("runs", "session_id")
    op.drop_index(op.f("ix_scenarios_session_id"), table_name="scenarios")
    op.drop_column("scenarios", "session_id")
